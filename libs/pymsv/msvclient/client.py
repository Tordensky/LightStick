# Written by Ingar Arntzen, Motion Corporation

import time
import threading
import traceback


import pymsv.util.timeouts as timeouts
from pymsv.util.mylog import MyLog

from pymsv.util.msvutil import P,V,A,T
import pymsv.msvserver.messages as messages
from pymsv.msvserver.messages import MsvCmd, MsgType
import pymsv.msvclient.connection as connection
from pymsv.msvserver.msvdb import compute_msv

try:
    import simplejson as json
except ImportError:
    import json

##############################################
# MSV
##############################################

class Msv:

    """
    MSV implements a thin wrapper for a single msv hosted by the
    MSVClient

    Assume msvclient to be ready for use
    """

    def __init__(self, msvclient, msvid):

        self._msvclient = msvclient
        self._msvid = msvid
        self._update_handlers = []

        # Check that msvclient is ready for operation
        if not self._msvclient.isReady():
            self._msvclient.waitForReady(0.2)
        assert self._msvclient.isReady(), "MSVclient not ready"
        # Hack to wait for msvclient connection
        if not self._msvclient.isConnected():
            time.sleep(0.2)
        assert self._msvclient.isConnected(), "MSVclient not connected"
        # Set up handlers
        self._msvclient.add_msv_handler(self._update_handler)

        # Check if specific msv is ready. If it is not, 
        # block until it is ready
        ok = self._msvclient.msv_is_ready(self._msvid)
        if not ok:
            res = self._msvclient.get([self._msvid], blocking=True)

    def _update_handler(self, msv_data):
        """Notify clients"""
        if msv_data['msvid'] == self._msvid:
            for handler in self._update_handlers:
                handler(msv_data)

    # API
        
    def is_ready(self):
        return self._msvclient.msv_is_ready(self._msvid)

    def is_moving(self):
        assert self.is_ready(), "MSV not ready"
        vector = self._msvclient.get_vector(self._msvid) 
        return vector[1] != 0 or vector[2] != 0

    def add_handler(self, handler):
        if handler not in self._update_handlers:
            self._update_handlers.append(handler)
    
    def remove_handler(self, handler):
        if handler in self._update_handlers:
            self._update_handlers.remove(handler)

    def get_vector(self):
        return self._msvclient.get_vector(self._msvid)

    def query(self):
        return self._msvclient.query(self._msvid)

    def update(self, p=None, v=None, a=None):
        if p == v == a == None:
            return
        msv_data_list = [{'msvid': self._msvid, 'vector': (p,v,a)}]
        self._client.update(msv_data_list)



##############################################
# CLIENT
##############################################

class Client(threading.Thread):

    def __init__(self, host, port=None, ws=True, stop_event=None):
        threading.Thread.__init__(self)
        
        if not host[-1] == "]" and host.rfind(":") > -1:
            # Not a literal IPv6 address and a port is given as part of the hostname
            pos = host.rfind(":")
            if pos > -1:
                port = int(host[pos+1:])
                host = host[:pos]

        self.log = MyLog().log

        # Synchronization
        self._client_lock = threading.Lock()
        self._stop_event = stop_event if stop_event != None else threading.Event()
        # Data structures
        self._cache = {} # msvid -> msv_data
        self._msv_handlers = []
        self._set_handlers = []
        # Timeout Manager
        self._tm = timeouts.TimeoutManager(stop_event=self._stop_event)
        # Server Clock Estimator
        self._clock = ServerClockEstimator()
        # Backoffticker
        self._ticker = BackoffTicker(self._tm, self._ontick)
        # Request management
        self._request_counter = 0
        self._pending_requests = {} # reqid -> (event, result) 
        # Connection to MsvServer
        if ws == True:
            self._conn = connection.WSConnection()
            if not port:
                self._serv_addr = (host, messages.CLIENT_ACCEPT_PORT)
            else:
                self._serv_addr = (host, port)
        else:
            self._conn = connection.Connection()
            if not port:
                self._serv_addr = (host, messages.FRONTEND_ACCEPT_PORT)
            else:
                self._serv_addr = (host, port)

        self._isReady = threading.Event()
        
    def isReady(self):
        return self._isReady.isSet()

    def waitForReady(self, timeout):
        return self._isReady.wait(timeout)

    def isConnected(self):
        """Added by Ingar to check if client is ready for operation.
        TODO: this should NOT be different from isReady
        """
        return self._conn and self._conn.is_connected()

    def stop(self):
        """Request that the client (main loop) stops"""
        self._stop_event.set()

    def run(self):
        """Main loop"""
        self._tm.start()
        #self._conn.connect(self._serv_addr)
        self._ticker.start()
        self._isReady.set()
        while not self._stop_event.is_set():
            if not self._conn.is_connected():
                try:
                    self._conn.connect(self._serv_addr)
                    
                    # Get whatever msvs we were already monitoring
                    self.log.debug("Reconnected, restoring subscriptions")
                    self.get(self._cache.keys())
                    
                except:
                    self.log.exception("Failed to connect, retrying later")
                    time.sleep(5)
                continue

            try:
                data = self._conn.get(1.0)
            except:
                self.log.exception("Failed to read, trying to reconnect")
                self._conn.close()
                continue

            if data != None:
                try:
                    msg = json.loads(data)
                    self._onmessage(msg)
                except ValueError:
                    self.log.exception("Bad message '%s'"%data)
                    continue
        # Cleanup
        self._conn.close()

    def _onmessage(self, msg):
        """Receive message from connection"""

        if msg['cmd'] == MsvCmd.PONG:
            cs, ss = msg['data']
            cr = time.time()
            self._clock.add_sample(cs, ss, cr)
            return
        
        if msg['type'] == MsgType.RESPONSE: # all responses except PONG

            # Update Msv Cache
            if msg['cmd'] in [MsvCmd.GET, MsvCmd.CREATE]:
                for msv_data in msg['data']:
                    self._cache[msv_data['msvid']] = msv_data

            try:
                # Hand over response to requesting client
                self._onresponse(msg)
            except Exception, e:
                print "MSV CLIENT ERROR, calling onresponse:",e
                traceback.print_exc()
                
            # Notify clients of set changes
            if msg['cmd'] in [MsvCmd.GET, MsvCmd.CREATE]:
                msvid_list = [x['msvid'] for x in msg['data']]
                for handler in self._set_handlers:
                    try:
                        handler(msvid_list, [])
                    except Exception, e:
                        print "MSV CLIENT ERROR on handler %s: %s"%(handler, e)
                        traceback.print_exc()
            return

        elif msg['type'] == MsgType.EVENT:
            self._onevent(msg)
            return

        print "Onmessage", msg

    def _ontick(self):
        """Send ping on tick"""
        cs = time.time()
        msg = {'type': MsgType.REQUEST, 'cmd': MsvCmd.PING, 'data': cs}
        self._conn.send(json.dumps(msg))

    def _dorequest(self, msg, blocking=False, handler=None, timeout=5.0):
        """Call handler asynchronously with (reqid, result).
        If handler not supplied, blocking call"""
        with self._client_lock:
            reqid = self._request_counter
            self._request_counter
            msg['tunnel'] = reqid
            if blocking:
                event = threading.Event()
                self._pending_requests[reqid] = (event, None)
                if self._conn.send(json.dumps(msg)) == 0:
                    # Send failed
                    print "Send went badly"
                    return None
                event.wait(timeout)
                if not event.isSet():
                    raise Exception("timeout")

                # wakeup
                if not self._pending_requests.has_key(reqid):
                    return # shutdown
                result = self._pending_requests[reqid]
                del self._pending_requests[reqid]
                return result                    
            else:
                self._pending_requests[reqid] = (None, handler)
                self._conn.send(json.dumps(msg))
                return reqid
        
    def _onresponse(self, msg):
        """Hand over result to client. Depending on
        what is stored in pending requests, blocked client
        is woken up, or result is delivered with handler invokation"""
        reqid = msg['tunnel']
        if not self._pending_requests.has_key(reqid):
            return
        event, handler = self._pending_requests[reqid]
        if event != None:
            # leave result to be picked up by blocked client
            self._pending_requests[reqid] = msg['data']
            # notify
            event.set()
        elif handler != None:
            del self._pending_requests[reqid]
            handler(reqid, msg['data'])

    def _onevent(self, msg):
        """Handle event"""
        # Update Cache
        for msv_data in msg['data']:
            self._cache[msv_data['msvid']] = msv_data
            trans = self._clock.get_time() - msv_data['vector'][T]
            print "Estimated Trans", trans
            diff = trans-self._clock.get_trans()
            print "Event trans - Best trans", diff
            ratio = diff/trans
            print "Does it matter?", ratio

       # Notify msv updates
        for handler in self._msv_handlers:
            for msv_data in msg['data']:
                try:
                    handler(msv_data)
                except Exception, e:
                    self.log.exception("Bad event handler '%s'"%handler)
                    traceback.print_exc()

    def create(self, msv_data_list, blocking=False, handler=False):
        """Create new msv - will be monitored"""
        msg = {'type': MsgType.REQUEST, 'cmd': MsvCmd.CREATE, 'data': msv_data_list}
        return self._dorequest(msg, blocking=blocking, handler=handler)

    def get(self, msvid_list, blocking=False, handler=None):
        """Request msvs - will be monitored"""
        if not msvid_list: return False
        msg = {'type': MsgType.REQUEST, 'cmd': MsvCmd.GET, 'data': msvid_list}
        return self._dorequest(msg, blocking=blocking, handler=handler)

    def release(self, msvid_list):
        """Release msvid from monitored set"""
        # Remove from cache
        for msvid in msvid_list:
            if self._cache.has_key(msvid):
                del self._cache[msvid]
        # Notify Locally
        for handler in self._set_handlers:
            handler([], msvid_list)
        # Release from server
        msg = {'type': MsgType.MESSAGE, 'cmd': MsvCmd.UNSUB, 'data': msvid_list}
        self._conn.send(json.dumps(msg))

    def msv_is_ready(self, msvid):
        """Check if particular msv is being monitored"""
        return self._cache.has_key(msvid)

    def get_vector(self, msvid):
        if self.msv_is_ready(msvid):
            msv_data = self._cache[msvid]
            v = msv_data['vector']
            # Convert to client time
            client_time = self._clock.get_client_time_from_server_time(v[T])
            return (v[P], v[V], v[A], client_time)

    def query(self, msvid):
        """Query msv for snapshot. Local operation. None returned if msv is
        not in cache, i.e. not being monitored."""
        msv_data = self._cache.get(msvid, None)
        if msv_data:
            # Convert initial vector to client time
            v = msv_data['vector']
            client_time = self._clock.get_client_time_from_server_time(v[T])
            return compute_msv((v[P], v[V], v[A], client_time), time.time())

    def update(self, msv_data_list):
        """Update msv. Not required that msv is being monitored, i.e. in cache."""
        msg = {'type': MsgType.MESSAGE, 'cmd': MsvCmd.UPDATE, 'data': msv_data_list}
        self._conn.send(json.dumps(msg))

    def list(self):
        """Return list of msvids for msvs currently being monitored."""
        return self._cache.keys()[:]

    def add_msv_handler(self, handler):
        """Register handler for msv updates"""
        if handler not in self._msv_handlers:
            self._msv_handlers.append(handler)

    def add_set_handler(self, handler):
        """Register handler for set changes
        Set handler is invoked with  two parameteters handler(added_msvids, released_msvids) 
        """
        if handler not in self._set_handlers:
            self._set_handlers.append(handler)



##############################################
#  BACKOFF TICKER
##############################################

SWITCH_SMALL_MEDIUM = 5
SWITCH_MEDIUM_LARGE = 10
SMALL_DELTA = .1
MEDIUM_DELTA = .5
LARGE_DELTA = 10

class BackoffTicker:

    def __init__(self, timeout_manager, tick_handler):
        self._tm = timeout_manager
        self._count = 0L
        self._tid = None
        self._tick_handler = tick_handler

    def start(self):
        self._tick()
    
    def _tick(self):
        self._count += 1
        if self._count < SWITCH_SMALL_MEDIUM:
            delta = SMALL_DELTA
	elif self._count < SWITCH_MEDIUM_LARGE:
            delta = MEDIUM_DELTA
        else:
            delta = LARGE_DELTA
        self._tid = self._tm.set_timeout(delta, lambda i,m: self._tick())
        self._tick_handler()

    def cancel(self):
        if self._tid != None:
            self._tm.cancel_timeout(self._tid)
        

##############################################
#  SERVER CLOCK
##############################################

class ServerClockEstimator:

    """This implements a simplistic server clock estimator where the
    clock skew is said to be the skew indicated by the sample with the lowest
    trans. Clock skew is defined according to the following formula.

    server_clock = client_clock + skew
    """

    def __init__(self, loglength=None):
        self._best_trans = 1000.0
        self._best_skew = 0.0
        self._log = []
        if loglength:
            self._N = loglength
        else:
            self._N = 30

    def add_sample(self, cs, ss, cr):
        trans = (cr-cs)/2.0
        skew = ss-((cr+cs)*0.5)
        self._add_sample(trans, skew)
        print "Trans %f Trans diff %f  Skew diff %f" % (trans, trans-self._best_trans, skew-self._best_skew)


    # TODO Policy
    # Recent samples with decent trans should be prioritized wrt skew to
    # detect clock skew
    # it matters when skew diff is the same order as trans
    # local net - trans 0.4 ms - skew diff up to 2ms



    def _add_sample(self, trans, skew):

        if len(self._log) > self._N:
            self._log.pop(0)
        self._log.append((trans, skew))
        # Recalculate best trans
        best_trans = 1000
        best_skew = None
        for trans, skew in self._log:
            if trans < best_trans:
                best_trans = trans
                best_skew = skew

        if best_skew != self._best_skew:
            print "skew updated", best_skew, best_trans
        
        self._best_trans = best_trans
        self._best_skew = best_skew


    def get_skew(self): return self._best_skew
    def get_trans(self): return self._best_trans

    def get_time(self):
        """Server time now"""
        return time.time() + self._best_skew

    def get_server_time_from_client_time(self, client_time):
        return client_time + self._best_skew

    def get_client_time_from_server_time(self, server_time):
        return server_time - self._best_skew
