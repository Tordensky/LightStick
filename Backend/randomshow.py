import json
import os
import random
from config import serverconfig


class RandomShow():
    def __init__(self):
        self.PATH = serverconfig.RANDOM_SHOW_FOLDER

    def getRandomShow(self):
        fileList = self._listAllShowFiles()

        randomShow = random.choice(fileList)
        with open(randomShow, "r") as file:
            data = file.read()
            return json.loads(data)

    def _listAllShowFiles(self):
        fileList = []
        for root, dirs, files in os.walk(self.PATH):
            for showFile in files:
                if showFile.endswith(".show"):
                    fileList.append(os.path.join(root, showFile))
        return fileList


if __name__ == "__main__":
    shows = RandomShow()
    print shows.getRandomShow()