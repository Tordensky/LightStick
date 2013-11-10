import json
import random
import threading
import time
import thread
import math
from randomshow import RandomShow
from config import serverconfig
from libs.pymsv.msvclient.client import Client, Msv


class CommandHandler():
    def __init__(self):
        self.messageNum = 0
        self.command = {}
        self.lock = threading.RLock()

        self.msvMsgIdController = MsvController("t0.mcorp.no:8091", 22)
        self.msvPlaybackController = MsvController("t0.mcorp.no:8091", 18)
        self.messageNum = self.msvMsgIdController.getCurrentMsvValue()

        self.isInRandomMode = True
        self.randomFileHelper = RandomShow()

        self.resetCounter = serverconfig.ENTER_RANDOM_MODE_AFTER_SEC
        self.startRandomMode()

    def startRandomMode(self):
        self.isInRandomMode = True
        thread.start_new_thread(self.randomHandler, ())

    def endRandomMode(self):
        self.isInRandomMode = False

    def setCommand(self, data, fromServer=True):
        if fromServer:
            self.isInRandomMode = False
            self.resetCounter = serverconfig.ENTER_RANDOM_MODE_AFTER_SEC

        self.messageNum += 1
        with self.lock:
            self.command = data
            self.msvMsgIdController.setMsvValue(self.messageNum)

    def getCommand(self):
        self.message = {"cmdNum": self.messageNum, "data": self.command}
        return json.dumps(self.message)

    def randomHandler(self):
        while True:
            while self.isInRandomMode:
                newShow = self.randomFileHelper.getRandomShow()
                timeStamp = int(math.floor(self.msvPlaybackController.getCurrentMsvValue()))
                timeStamp += serverconfig.RANDOM_BPM_DELAY_NEXT_SHOW

                newShow["MSV_TIME"] = timeStamp

                self.setCommand(newShow, fromServer=False)

                randomInterval = random.randrange(serverconfig.RANDOM_INTERVAL_SEC_MIN,
                                                  serverconfig.RANDOM_INTERVAL_SEC_MAX)
                time.sleep(randomInterval)

            while not self.isInRandomMode:
                time.sleep(5)
                self.resetCounter -= 5
                if self.resetCounter <= 0:
                    self.isInRandomMode = True


class MsvController():
    def __init__(self, host, msvid):
        print "INITALIZE MSV"
        self.HOST = host
        self.MSVID = msvid

        try:
            self._client = Client(self.HOST)
            self._client.start()
            self._msv = Msv(self._client, self.MSVID)
            self._msv.add_handler(self.update_handler)
        except AssertionError:
            print "MSV ERROR"
            exit()

    def setMsvValue(self, value):
        self.__update(value)

    def getCurrentMsvValue(self):
        return int(self._msv.query()[0])

    def __update(self, value):
        msv_data_list = [{'msvid': self.MSVID, 'vector': (value, 0.0, 0.0)}]
        self._client.update(msv_data_list)

    def update_handler(self, msv_data):
        pass







