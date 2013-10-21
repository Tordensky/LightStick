import json
import threading
from config import APPLICATION_BASE_PATH
from libs.pymsv.msvclient.client import Client, Msv


class CommandHandler():
    def __init__(self):
        self.messageNum = 0
        self.command = {}
        self.lock = threading.RLock()

        self.msvController = MsvController()
        self.messageNum = self.msvController.getCurrentMsvValue()
        print self.messageNum

    def setCommand(self, data):
        self.messageNum += 1
        with self.lock:
            self.command = json.loads(data)
            self.msvController.setMsvValue(self.messageNum)

    def getCommand(self):
        self.message = {"cmdNum": self.messageNum, "data": self.command}
        return json.dumps(self.message)


class MsvController():
    HOST = "t0.mcorp.no:8091"
    MSVID = 22

    def __init__(self):
        print "INITALIZE MSV"

        try:
            self._client = Client(self.HOST)
            self._client.start()
            self._msv = Msv(self._client, self.MSVID)
            self._msv.add_handler(self.update_handler)
        except AssertionError:
            print "MSV ERROR"

    def setMsvValue(self, value):
        print "msv new value", value
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
                return  data


