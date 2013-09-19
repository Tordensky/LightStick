# Written by Ingar Arntzen, Norut

import threading
import code
import msvserver.messages as messages
import msvclient.client as client

USAGE = """

CONNECTING
- %s

USAGE
- list() - list set members (msvids)
- query(msvid) - query MSV for snapshot
- update(msvid,p=1.0,v=0.0,a=0.0) - update MSV
- get(msvid) - start monitoring
- add_set_handler(handler(added, removed))
- add_msv_handler(handler(msv_data))
- add_state_handler(handler(state))
"""

##############################################
# CONSOLE CLIENT
##############################################

class ConsoleClient:

    """
    This implements a python-console to the msv client.
    """

    def __init__(self, host, ws=True, stop_event=None):
        self._stop_event = stop_event if stop_event != None else threading.Event()
        self._client = client.Client(host, ws=ws, stop_event=self._stop_event)
        self._client.start()
        #self._client_thread = threading.Thread(target=self._client.run)
        #self._client_thread.daemon = False # graceful shutdown

    def stop(self):
        self._stop_event.set()

    def run(self):
        #self._client_thread.start()
        ns = {
            'get': self.get,
            'create': self.create,
            'query': self.query,
            'release': self.release,
            'update': self.update,
            'list': self.list,
            'add_msv_handler': self.add_msv_handler,
            'add_set_handler': self.add_set_handler,
            }
        code.interact(local=ns)


    def join(self, timeout=None):
        self._client.join(timeout=timeout)
        pass

    def create(self, range=None):
        if range:
            msv_data_list = [{'range': range}]
        else:
            msv_data_list = [{}]
        return self._client.create(msv_data_list, blocking=True)

    def get(self, msvid_list):
        if type(msvid_list) == type(1):
            msvid_list = [msvid_list]
        return self._client.get(msvid_list, blocking=True)

    def release(self, msvid):
        self._client.release([msvid])

    def query(self, msvid):
        return self._client.query(msvid)

    def update(self, msvid, p=None, v=None, a=None):
        if p == v == a == None:
            return
        msv_data_list = [{'msvid': msvid, 'vector': (p,v,a)}]
        self._client.update(msv_data_list)

    def list(self):
        return self._client.list()

    def add_msv_handler(self, handler):
        return self._client.add_msv_handler(handler)

    def add_set_handler(self, handler):
        return self._client.add_set_handler(handler)


##############################################
# MAIN
##############################################

if __name__ == '__main__':

    HOST = "venus.itek.norut.no"
    
    import sys
    import urlparse

    if len(sys.argv) > 1:
        try:            
            HOST = sys.argv[1]
        except:
            pass

    print USAGE % HOST
    cc = ConsoleClient(HOST)
    try:
        cc.run()
    except KeyboardInterrupt:
        print
    cc.stop()
    cc.join()
    print "Done"
