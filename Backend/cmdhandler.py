import json
import threading


class CommandHandler():
    def __init__(self):
        self.messageNum = 0

        self.command = {}
        self.lock = threading.RLock()

    def setCommand(self, data):
        self.messageNum += 1
        with self.lock:
            self.command = json.loads(data)

    def getCommand(self):
        self.message = {"cmdNum": self.messageNum, "data": self.command}
        return json.dumps(self.message)


if __name__ == "__main__":
    pass