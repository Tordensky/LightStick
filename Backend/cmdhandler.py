import json
import threading


class CommandHandler():
    def __init__(self):
        self.command = {"Start": 123456.1234, "Show": [{"Duration": 8, "Color": [255, 222, 333]}]}
        self.lock = threading.RLock()

    def setCommand(self, data):
        with self.lock:
            self.command = json.dumps(data)

    def getCommand(self):
        with self.lock:
            cmd = self.command
        return cmd


if __name__ == "__main__":
    pass