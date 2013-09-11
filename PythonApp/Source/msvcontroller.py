# Based on the code written by Ingar Arntzen, Norut & Motion Corporation
import os

import threading
import time
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget

from msvclient.client import Client, Msv

Builder.load_file(os.getenv("FILE_PATH") + "/msvcontroller.kv")


class SimpleMsvController(Widget):
    HOST = "mcorp.no:8091"
    MSVID = 18

    msvPosition = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super(SimpleMsvController, self).__init__(**kwargs)
        self._stop_event = threading.Event()
        self._client = Client(self.HOST)
        self._client.start()
        self._msv = Msv(self._client, self.MSVID)
        self._msv.add_handler(self.update_handler)

        #self.update(18, 0, 1, 0)

        self.lock = threading.RLock()

        self.msvThread = threading.Thread(target=self.run)

        self.msvThread.start()

    def update_handler(self, msv_data):
        #print "Update", msv_data
        pass

    def update(self, msvid, p=None, v=None, a=None):
        if p is v is a is None:
            return
        msv_data_list = [{'msvid': msvid, 'vector': (p, v, a)}]
        self._client.update(msv_data_list)

    def stop(self):
        self._client.stop()
        self._stop_event.set()

    def join(self):
        self._client.join()

    def updateScreen(self, value):
        with self.lock:
            self.msvPosition = round(value, 3)

    def run(self, *args):
        while not self._stop_event.is_set():
            vector = self._msv.query()
            #print vector

            self.updateScreen(vector[0])

            time.sleep(0.1)




    
#################################################
# MAIN
#################################################

if __name__ == '__main__':
    
    HOST = "mcorp.no:8091"
    MSVID = 18

    s = SimpleMsvController(HOST, MSVID)
    try:
        s.run()
    finally:
        s.stop()
        s.join()
