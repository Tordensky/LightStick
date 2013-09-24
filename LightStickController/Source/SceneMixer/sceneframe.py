from scnconfig import EffectNames


class SceneFrame():
    def __init__(self):
        self.__fadeTime = None
        self.__sceneTime = None

        self.__effects = {}

    def addEffect(self, Effect):
        effectName = Effect.getEffectName()
        self.__effects[effectName] = Effect

    def getEffect(self, name):
        if self.hasEffect(name):
            return self.__effects[name]
        return None

    def getEffects(self):
        effectList = []
        for key, value in self.__effects.iteritems():
            effectList.append(value)
        return effectList

    def hasEffect(self, name):
        return name in self.__effects

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


class Effect():
    def __init__(self, name):
        self.__name = name

    def getEffectName(self):
        return self.__name


class ColorEffect(Effect):

    def __init__(self):
        Effect.__init__(self, EffectNames.COLOR_EFFECT)
        self.__color = (1.0, 1.0, 1.0, 1.0)

    def getKivyColor(self):
        return self.__color

    def setKivyColor(self, color):
        self.__color = color

    def getHexColor(self):
        # TODO
        pass
