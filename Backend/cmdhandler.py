from collections import defaultdict
import json
import random
import threading
import time
import thread
import math
from randomshow import RandomShow
from config import serverconfig
from config import APPLICATION_BASE_PATH
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
        self.startRandomMode()

    def startRandomMode(self):
        self.isInRandomMode = True
        thread.start_new_thread(self.randomHandler, ())

    def endRandomMode(self):
        self.isInRandomMode = False

    def setCommand(self, data):
        self.messageNum += 1
        with self.lock:
            self.command = data
            self.msvMsgIdController.setMsvValue(self.messageNum)

    def getCommand(self):
        self.message = {"cmdNum": self.messageNum, "data": self.command}
        return json.dumps(self.message)

    def randomHandler(self):
        while self.isInRandomMode:
            newShow = self.randomFileHelper.getRandomShow()
            timeStamp = int(math.floor(self.msvPlaybackController.getCurrentMsvValue()))
            timeStamp += serverconfig.RANDOM_START_DELAY

            newShow["MSV_TIME"] = timeStamp

            self.setCommand(newShow)

            randomInterval = random.randrange(serverconfig.RANDOM_INTERVAL_SEC_MIN,
                                              serverconfig.RANDOM_INTERVAL_SEC_MAX)
            time.sleep(randomInterval)


class MsvController():
    def __init__(self, host, msvid):
        print "INITALIZE MSV"

        #self.HOST = "t0.mcorp.no:8091"
        self.HOST = host
        #self.MSVID = 22
        self.MSVID = msvid

        try:
            self._client = Client(self.HOST)
            self._client.start()
            self._msv = Msv(self._client, self.MSVID)
            self._msv.add_handler(self.update_handler)
        except AssertionError:
            print "MSV ERROR"

    def setMsvValue(self, value):
        self.__update(value)

    def getCurrentMsvValue(self):
        return int(self._msv.query()[0])

    def __update(self, value):
        msv_data_list = [{'msvid': self.MSVID, 'vector': (value, 0.0, 0.0)}]
        self._client.update(msv_data_list)

    def update_handler(self, msv_data):
        pass


class FileCash():
    def __init__(self):
        self.cache = {}
        self.lock = threading.RLock()

    def getFile(self, filename):
        with self.lock:
            if filename in self.cache:
                return self.cache[filename]
            else:
                f = open(APPLICATION_BASE_PATH + filename, 'rb')
                data = f.read()
                # TODO ENABLE TO ADD CACHING!
                #self.cache[filename] = data
                return data


class Monitor():
    def __init__(self):
        self.logFileName = "log/cmdLogFile" + str(int(time.time())) + ".log"
        self.dropBoxFileName = "B:/Dropbox/Privat/insomnialog/" + self.logFileName

        self.heartbeats = 0
        self.ids = defaultdict(int)

        self.lock = threading.RLock()
        self.writeLock = threading.RLock()

        self.logInterval = 60000

        headerLine = "STARTING SERVER: " + str(time.asctime()) + "\n" \
                     "INTERVAL: " + str(self.logInterval) + "\n#####\n"
        self.appendToFile(headerLine)

        thread.start_new_thread(self.idLogger, ())

    def addID(self, clientID):
        with self.lock:
            self.ids[clientID] += 1

    def getIDsAndReset(self):
        with self.lock:
            ids = self.ids
            self.ids = defaultdict(int)
            return ids

    def idLogger(self):
        while True:
            clients = self.getIDsAndReset()
            logRecord = {"time": time.asctime(), "num clients": len(clients), "history": clients}
            self.appendToFile(json.dumps(logRecord))
            time.sleep(self.logInterval / 1000.0)

    def appendToFile(self, line):
        with self.writeLock:
            with open(self.logFileName, "a") as stream:
                stream.write(line + "\n")

            with open(self.dropBoxFileName, "a") as stream:
                stream.write(line + "\n")





