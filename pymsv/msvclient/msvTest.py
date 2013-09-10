# Written by Ingar Arntzen, Norut & Motion Corporation

import threading
import time

from msvclient.client import Client, Msv


class SimpleMSV:

    """Visualise a single MSV in the terminal"""

    def __init__(self, host, msvid):
        self._stop_event = threading.Event()
        self._client = Client(host)
        self._client.start()
        self._msv = Msv(self._client, msvid)
        self._msv.add_handler(self.update_handler)

    def update_handler(self, msv_data):
        print "Update", msv_data
        pass

    def update(self, msvid, p=None, v=None, a=None):
        if p == v == a == None:
            return
        msv_data_list = [{'msvid': msvid, 'vector': (p, v, a)}]
        self._client.update(msv_data_list)

    def stop(self):
        self._client.stop()
        self._stop_event.set()

    def join(self):
        self._client.join()

    def run(self):

        self.update(18, 0, 1, 0)
        while not self._stop_event.is_set():
            vector = self._msv.query()
            print vector

            time.sleep(0.1)

    
#################################################
# MAIN
#################################################

if __name__ == '__main__':
    
    HOST = "mcorp.no:8091"
    MSVID = 18

    s = SimpleMSV(HOST, MSVID)
    try:
        s.run()
    finally:
        s.stop()
        s.join()
