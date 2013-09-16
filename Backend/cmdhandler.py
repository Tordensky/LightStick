import json
import threading
import random


class CommandHandler():
    def __init__(self):
        self.messageNum = 0

        self.command = {}
        self.lock = threading.RLock()

    def setCommand(self, data):
        with self.lock:
            self.command = json.loads(data)

    def getCommand(self):
        self.messageNum += 1
        self.command["cmdNum"] = self.messageNum
        with self.lock:
            cmd = self.command
        return json.dumps(cmd)


if __name__ == "__main__":
    pass