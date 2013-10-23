# Based on the code written by Ingar Arntzen, Norut & Motion Corporation
from collections import defaultdict
import json
import os
import pprint

import threading
import time
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import NumericProperty, DictProperty
from kivy.uix.widget import Widget
import math
from HttpWebClient import HttpClient
from SceneMixer import Popups

from libs.pymsv.msvclient.client import Client, Msv


Builder.load_file(os.getenv("FILE_PATH") + "/msvcontroller.kv")


class SimpleMsvController(Widget, EventDispatcher):
    HOST = "t0.mcorp.no:8091"
    MSVID = 18

    msvVelocity = NumericProperty(0.0)
    msvPosition = NumericProperty(0.0)
    msvAcceleration = NumericProperty(0.0)
    currentBPM = NumericProperty(0.0)

    currentMsg = DictProperty({})
    delay = NumericProperty(4)

    def __init__(self, **kwargs):
        self.register_event_type('on_set_new_show_from_a')
        self.register_event_type('on_set_new_show_from_b')
        super(SimpleMsvController, self).__init__(**kwargs)
        self.source = None

        self.__set_new_show = False
        self.__set_new_bpm = False

        self.bpm = defaultdict(float)
        self.httpClient = HttpClient("localhost", 8080)

        try:
            self._stop_event = threading.Event()
            self._client = Client(self.HOST)
            self._client.start()
            self._msv = Msv(self._client, self.MSVID)
            self._msv.add_handler(self.update_handler)

            self.lock = threading.RLock()
            self.msvThread = threading.Thread(target=self.run)
            self.msvThread.start()
        except AssertionError:
            print "MSV ERROR"
            Clock.schedule_once(self.showMsvErrorPopup, 1 / 2.0)

    def showMsvErrorPopup(self, *args):
        popup = Popups.errorPopup(titleLabel="MSV ERROR",
                                  text="Error: Could not connect to MSV service!")
        popup.open()

    def showServerErrorPopup(self, statusCode, *args):
        if statusCode == -1:
            errorText = "Error: Could not connect to server!"
        else:
            errorText = "Error. Bad request!\nGot response status: " + str(statusCode) + " expected: 200"
        popup = Popups.errorPopup(titleLabel="SERVER ERROR",
                                  text=errorText)
        popup.open()

    def delayUp(self):
        print "delay up"
        self.delay += 1

    def delayDown(self):
        print "delay down"
        if self.delay > 1:
            self.delay -= 1

    def on_whole_beat(self, source):
        if self.__set_new_bpm and self.source == source:
            self.setVelocityFromBPM(self.bpm[source])
            self.__set_new_bpm = False

    def on_set_new_show_from_a(self):
        pass

    def on_set_new_show_from_b(self):
        pass

    def setSourceForBpm(self, source):
        self.source = source

        if source == "A":
            self.dispatch('on_set_new_show_from_a')
        elif source == "B":
            self.dispatch('on_set_new_show_from_b')

    def setBpmFromSource(self, source):
        self.source = source
        self.__set_new_bpm = True

    def sendSceneToServer(self, msg):
        msg["MSV_TIME"] = int(math.ceil(self.msvPosition)) + int(self.delay)  # Todo make dynamic delay for start
        msg = json.dumps(msg)
        self.httpClient.postJson(jsonMessage=msg, url="/command", callback=self.postCallback)

    def postCallback(self, responseCode, *args):
        if responseCode != 200:
            self.showServerErrorPopup(responseCode)

    def setBpm(self, bpm, source):
        self.bpm[source] = bpm
        print bpm, source

    def setVelocityFromBPM(self, bpm):
        print "Set new velocity"
        velocity = bpm / 60.0
        self.update(18, int(self.msvPosition), velocity, 0)

    def on_msvVelocity(self, *args):
        print args[1]

    def update_handler(self, msv_data):
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

    def updateScreen(self, pos, vel, acc):
        with self.lock:
            self.msvPosition = round(pos, 1)
            self.msvVelocity = round(vel, 3)
            self.msvAcceleration = round(acc, 3)
            self.currentBPM = round(60.0 * vel, 1)

    def run(self, *args):
        while not self._stop_event.is_set():
            vector = self._msv.query()

            self.updateScreen(vector[0], vector[1], vector[2])

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
