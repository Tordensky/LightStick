import json
import threading


class CommandHandler():
    def __init__(self):
        self.command = None
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