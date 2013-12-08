# Based on the code written by Ingar Arntzen, Norut & Motion Corporation
from collections import defaultdict
import json
import os
import math
from sqlite3 import Time
import threading
import time

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import NumericProperty, DictProperty
from kivy.uix.widget import Widget
from HttpWebClient import HttpClient
from SceneMixer import Popups

from libs.pymsv.msvclient.client import Client, Msv


Builder.load_file(os.getenv("FILE_PATH") + "/msvcontroller.kv")


class SimpleMsvController(Widget, EventDispatcher):
    HOST = "t0.mcorp.no:8091"
    MSVID = 18

    msvPosition = NumericProperty(0.0)
    currentBPM = NumericProperty(0.0)

    currentMsg = DictProperty({})
    delay = NumericProperty(4)

    def __init__(self, **kwargs):
        self.register_event_type('on_set_new_show_from_a')
        self.register_event_type('on_set_new_show_from_b')
        super(SimpleMsvController, self).__init__(**kwargs)
        self.source = None

        self.__set_new_show = False
        self._set_new_bpm = False

        self.bpm = defaultdict(float)
        self.httpClient = HttpClient("129.242.22.10", 8080)

        self.window = Window.bind(on_close=self.stop)

        self._stop_event = threading.Event()
        self.lock = threading.RLock()
        self._conn_tries = 3
        while self._conn_tries > 0:
            try:
                self._client = Client(self.HOST)
                self._client.start()
                self._msv = Msv(self._client, self.MSVID)
                self._msv.add_handler(self.update_handler)

                self.msvThread = threading.Thread(target=self.run)
                self.msvThread.start()

                self._conn_tries = 0
            except AssertionError:
                self._conn_tries -= 1
                if self._conn_tries == 0:
                    Clock.schedule_once(self.showMsvErrorPopup, 1 / 2.0)
                    Time.sleep(1)
                else:
                    print "Could not connect to msv server. Retries, Retries left: " + self._conn_tries

    def showMsvErrorPopup(self, *args):
        popup = Popups.errorPopup(titleLabel="MSV ERROR",
                                  text="Error: Could not connect to MSV service!")
        popup.open()

    def showServerErrorPopup(self, statusCode, *args):
        if statusCode == -1:
            errorText = "Error: Could not connect to server!"
        else:
            errorText = "Error. Bad request!\n" \
                        "Got response status: " \
                        "" + str(statusCode) + " " \
                        "expected: 200"
        popup = Popups.errorPopup(titleLabel="SERVER ERROR",
                                  text=errorText)
        popup.open()

    def delayUp(self):
        self.delay += 1

    def delayDown(self):
        if self.delay > 0:
            self.delay -= 1

    def on_whole_beat(self, source):
        if self._set_new_bpm and self.source == source:
            self.setMsvSpeed(self.bpm[source])
            self._set_new_bpm = False

    # EVENT USED IN .KV FILES
    def on_set_new_show_from_a(self):
        pass

    # EVENT USED IN .KV FILES
    def on_set_new_show_from_b(self):
        pass

    # EVENT USED IN .KV FILES
    def update_handler(self, msv_data):
        pass

    def setSourceForBpm(self, source):
        self.source = source
        if source == "A":
            self.dispatch('on_set_new_show_from_a')
        elif source == "B":
            self.dispatch('on_set_new_show_from_b')

    def setBpmFromSource(self, source_id):
        self.source = source_id
        self._set_new_bpm = True

    def sendSceneToServer(self, msg):
        msg["MSV_TIME"] = int(math.ceil(self.msvPosition)) + int(self.delay)
        msg = json.dumps(msg)
        self.httpClient.postJson(jsonMessage=msg, url="/command", callback=self.postCallback)

    def postCallback(self, responseCode, *args):
        if responseCode != 200:
            self.showServerErrorPopup(responseCode)

    def setBpm(self, bpm, sourceId):
        self.bpm[sourceId] = bpm

    def setMsvSpeed(self, bpm):
        velocity = bpm / 60.0
        self.updateMSV(18, int(self.msvPosition), velocity, 0)

    def updateMSV(self, msvid, p=None, v=None, a=None):
        if p is v is a is None:
            return
        msv_data_list = [{'msvid': msvid, 'vector': (p, v, a)}]
        self._client.update(msv_data_list)

    def updateScreen(self, pos, vel, acc):
        with self.lock:
            self.msvPosition = round(pos, 1)
            self.currentBPM = round(60.0 * vel, 1)

    def run(self, *args):
        while not self._stop_event.is_set():
            vector = self._msv.query()

            self.updateScreen(vector[0], vector[1], vector[2])
            time.sleep(0.1)

    def stop(self, *args):
        self._client.stop()
        self._stop_event.set()
