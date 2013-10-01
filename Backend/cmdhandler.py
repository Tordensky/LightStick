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
        self.command["cmdNum"] = self.messageNum
        with self.lock:
            cmd = self.command
        return json.dumps(cmd)


if __name__ == "__main__":
    pass