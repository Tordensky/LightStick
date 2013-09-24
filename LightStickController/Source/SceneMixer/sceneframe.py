

class SceneFrame():
    def __init__(self):
        self.__fadeTime = None
        self.__sceneTime = None

    def getFadeTime(self):
        return self.__fadeTime

    def setFadeTime(self, fadeTime):
        if self.__fadeTime > self.__sceneTime:
            self.__sceneTime = self.__fadeTime
        self.__fadeTime = float(fadeTime)

    def getSceneTime(self):
        return self.__sceneTime

    def setSceneTime(self, sceneTime):
        self.__sceneTime = float(sceneTime)

