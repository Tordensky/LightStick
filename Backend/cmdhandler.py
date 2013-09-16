import json
import threading
import random


class CommandHandler():
    def __init__(self):
        self.messageNum = 0

        self.command = None
        self.lock = threading.RLock()

        # Random for testing
        self.colors = ["#ff0000", "#00ff00", "#0000ff"]

    def setCommand(self, data):
        with self.lock:
            self.command = json.dumps(data)

    def getCommand(self):
        self.messageNum += 1
        self.command = {"command": {"color": random.choice(self.colors)}, "msg": self.messageNum}
        with self.lock:
            cmd = self.command
        return json.dumps(cmd)


if __name__ == "__main__":
    pass