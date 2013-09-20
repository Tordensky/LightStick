import random


class SceneFrame():
    def __init__(self):
        self.__fadeTime = random.randint(1, 100)
        self.__sceneTime = random.randint(1, 100)

    def getFadeTime(self):
        return self.__fadeTime

    def setFadeTime(self, fadeTime):
        self.__fadeTime = float(fadeTime)

    def getSceneTime(self):
        return self.__sceneTime

    def setSceneTime(self, sceneTime):
        self.__sceneTime = float(sceneTime)

