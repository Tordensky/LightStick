# Written by Ingar Arntzen, Motion Corporation

"""
This implements a python client for msvserver (v3)

"""
import time
import socket
import select
import traceback
import urllib
import Queue
import threading
try:
    import simplejson as json
except:
    import json
import pymsv.msvserver.messages as messages
from pymsv.msvserver.messages import relay_parse, relay_serialize
from pymsv.msvserver.messages import WS, ws_parse, ws_serialize


def connect(serv_addr):
    """Create sock and connect"""
    for res in socket.getaddrinfo(serv_addr[0],
                                  serv_addr[1],
                                  socket.AF_UNSPEC,
                                  socket.SOCK_STREAM, 0):
        af, socktype, proto, canonname, sa = res
        sock = socket.socket(af, socktype, proto)            
        sock.connect(sa)
        return sock
    raise Exception("Could not connect to %" % str(sa))





##############################################
# CONNECTION
##############################################

class Connection:
    
    """
    This implements a client connection to the msv server,
    including blocking primitives for sending and receiving messages.
    """
    def __init__(self):
        self._sock = None
        self._data = ""
        self._buf = []
        self._is_connected = False

    def connect(self, serv_addr):
        """Connect to server""" 
        self._sock = connect(serv_addr)
        if self._sock:
            self._is_connected = True
        return self._is_connected

    def is_connected(self):
        return self._is_connected
    
    def get_sock(self):
        """Return socket object"""
        return self._sock

    def send(self, string_data):
        """Send string data"""
        if self._is_connected:
            data = self.serialize(string_data)
            self._sock.send(data)

    def parse(self, data):
        """Parse message according to msvserver socket protocol."""
        return relay_parse(data)

    def serialize(self, data):
        """Serialize data according to msvserver socket protocol."""
        return relay_serialize(data)

    def get(self, delta):
        """
        Blocking receive. Delta specifies timeout.
        If timeout expires None is retured.
        Infinite Timeout not supported - must be specified 
        Received message is string data
        """

        if not self._buf:
            try:
                timeout = time.time() + delta
                while True:
                    remaining = timeout-time.time()
                    if remaining <= 0:
                        break
                    r,w,e = select.select([self._sock],[],[], remaining)
                    if self._sock in r:
                        data = self._sock.recv(1024)
                        if data:
                            self._data += data
                            while True:
                                payload, self._data = self.parse(self._data)
                                if payload == None:
                                    break
                                self._buf.append(payload)
                        else:
                            raise Exception("Connection lost")
                            
                        break
            except (select.error, socket.error) as e:
                traceback.print_exc()
        if self._buf:
            return self._buf.pop(0)

    def close(self):
        """
        Close Connection.
        """
        self._is_connected = False
        if self._sock:
            self._sock.close()
            self._sock = None

##############################################
# WS CONNECTION
##############################################

class WSConnection(Connection):
    
    """
    This implements a websocket client connection to the msv server,
    including blocking primitives for sending and receiving messages.
    """

    def connect(self, serv_addr):
        """
        Override connect to implement websocket handshake.
        """
        Connection.connect(self, serv_addr)

        # WebSocket Handshake
        request_headers = messages.make_ws_request_headers(serv_addr)
        self._ws_key = request_headers["sec-websocket-key"]
        request_data = messages.make_http_request('GET', '/',
                                                  headers=request_headers)

        self._sock.send(request_data)
        data = self._sock.recv(1024)            
        msg, data = messages.http_parse(data)
        if msg == None:
            self._sock.close()
            self._sock = None
            self._is_connected = False
            return

        response_headers, body = msg
        # Verify handshake response
        verified = messages.verify_ws_response_headers(self._ws_key, 
                                                       response_headers) 
        if verified:
            self._is_connected = True
        else:
            self._is_connected = False
            self._sock.close()
            self._sock = None

        return self._is_connected


    def parse(self, data):
        """
        Override parsing to extract websocket payload 
        """
        msg, data = ws_parse(data)
        if msg == None:
            return msg, data
        # Check websocket message type
        if msg['opcode'] == WS.OPCODE_TEXT:
            return msg['payload'], data
        else:
            return None, data

    def serialize(self, payload):
        """
        Serialize according to websocket protocol.
        """
        return ws_serialize(payload, mask=True)




##############################################
# JSON CONNECTION 
##############################################

class JSONConnection(Connection):

    def send(self, msg):
        data = json.dumps(msg)
        return Connection.send(self, data)    

    def get(self, delta):
        data = Connection.get(self, delta)
        if data:
            return json.loads(data)
        

##############################################
# JSON WS CONNECTION 
##############################################

class JSONWSConnection(WSConnection):

    def send(self, msg):
        data = json.dumps(msg)
        return WSConnection.send(self, data)    
    def get(self, delta):
        data = WSConnection.get(self, delta)
        if data:
            return json.loads(data)



##############################################
# JSON HTTP CONNECTION
##############################################

class JSONHTTPConnection:

    """
    This emulates a duplex connection using (abusing) HTTP GET
    request-response pattern. Traffic from client to server is
    transported using regular HTTP GETS, whereas longpolling is used
    for timely datatransfer in the opposite direction
    """

    def __init__(self):
        self._worker_addr = None
        self._sid = None
        self._lp_sock = None
        self._queue = Queue.Queue()
        self._stop_event = threading.Event()

    def close(self):
        """Close connection"""
        self._stop_event.set()
        if self._lp_sock:
            self._lp_sock.close()
            self._lp_sock = None

    def connect(self, serv_addr):
        """Connect to server""" 
        sock = connect(serv_addr)

        # HTTP Handshake
        request_data = messages.make_http_request('GET', '/createsession')
        data = ''
        success = True
        try:
            sock.send(request_data)
            payload = self._wait_response(sock, wait=2.0)
            if not payload:
                success = False
            else:
                response_headers, body = payload
                if response_headers['code'] != 200:
                    success = False
                else:
                    msg = json.loads(body)
                    self._worker_addr= (serv_addr[0], msg['port'])
                    self._sid = msg['sid'] 
                    self._longpoll()
            return success
        except socket.error as e:            
            return False
        finally:
            sock.close()

    def get(self, delta):
        """
        Blocking receive. Timeout specifies block timeout.
        If timeout expires None is retured.
        Infinite (None) Timeout not supported - must be specified 
        Received message is string data
        """
        if not delta:
            return
        try:
            return self._queue.get(timeout=delta)
        except Queue.Empty:
            return None

    def send(self, msg):
        """Send message - may be string data or python object"""
        if not (self._sid and self._worker_addr):
            return False
        return self._do_request('op', msg=msg)

    def _longpoll(self):
        """Issue a longpoll request"""
        if not (self._sid and self._worker_addr):
            return False
        if self._lp_sock:
            self._lp_sock.close()
            self._lp_sock = None
        return self._do_request('lp')

    def _do_request(self, op, msg=None):
        if op not in ['op', 'lp']:
            return False
        if not msg: 
            msg = {}
        msg['op'] = op
        msg['sid'] = self._sid
        path = '/?data=' + urllib.quote(json.dumps(msg))
        http_request = messages.make_http_request('GET', path)
        try:
            sock = connect(self._worker_addr)
            sock.send(http_request)
            if op == 'op':
                f = lambda : self._wait_op(sock)
            else:
                self._lp_sock = sock
                f = lambda : self._wait_lp(sock)
            t = threading.Thread(target=f)
            t.setDaemon(True)
            t.start()
        except:
            traceback.exc()
            return False
        return True

    def _wait_op(self, sock):
        """Wait for the completion of a regular operation"""
        payload = self._wait_response(sock, wait=2.0)
        if not payload:
            raise Exception("Request timed out")
        else:
            header_map, body = payload            
            if body:
                msg = json.loads(body)
                if msg and msg.has_key('type'):
                    self._queue.put(msg)
        sock.close()

    def _wait_lp(self, sock):
        """Wait for the completion of a longpoll operation"""
        payload = self._wait_response(sock, wait=40)
        if not payload:
            pass
        else:
            # New longpoll
            if not self._stop_event.is_set():
                self._longpoll()
            # Empty messages are not forwarded
            header_map, body = payload
            if body:
                msg = json.loads(body)
                if msg and msg.has_key('type'):
                    self._queue.put(msg)
        sock.close()

    def _wait_response(self, sock, wait=1.0):
        """
        Wait maximum delta seconds for a single http response on socket
        This is run by a thread.
        """
        try:
            timeout = time.time() + wait
            recv_data = ''
            while not self._stop_event.is_set():
                remaining = min(timeout-time.time(), 1.0)
                if remaining <= 0:
                    break
                r,w,e = select.select([sock], [], [sock], remaining)
                if sock in r:
                    data = sock.recv(1024)
                    if data:
                        recv_data += data
                        payload, recv_data = messages.http_parse(recv_data)
                        if payload:
                            # completely read
                            return payload
                        else:
                            # not completely read yet
                            continue
                    else:
                        # readable yet no data
                        print "hello"
                        break
                elif sock in e:
                    print "errro"
                else:
                    # not readable yet (early timeout)
                    continue
        except (select.error, socket.error) as e:
            traceback.print_exc()
        finally:
            sock.close()










    
