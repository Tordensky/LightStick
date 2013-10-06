import math
from serializer import Serializable
from scnconfig import EffectNames, SerializedKeys


class SceneFrame(Serializable):
    def __init__(self):
        self.__fadeTime = None
        self.__sceneTime = None

        self.__effects = {}

    def addEffect(self, Effect):
        effectName = Effect.get_effect_name()
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
        print "setsfade,", fadeTime
        if self.__fadeTime > self.__sceneTime:
            self.__sceneTime = self.__fadeTime
        self.__fadeTime = float(fadeTime)

    def getSceneTime(self):
        return self.__sceneTime

    def setSceneTime(self, sceneTime):
        print "setsScene,", sceneTime
        self.__sceneTime = float(sceneTime)

    def serialize_to_dict(self):
        serDict = Serializable.serialize_to_dict(self)
        serDict[SerializedKeys.FADE_TIME] = self.__fadeTime
        serDict[SerializedKeys.SCENE_TIME] = self.__sceneTime

        serDict[SerializedKeys.EFFECT_LIST] = []
        for effect in self.getEffects():
            serDict[SerializedKeys.EFFECT_LIST].append(effect.serialize_to_dict())

        return serDict


class Effect(Serializable):
    def __init__(self, name):
        self.__name = name

    def get_effect_name(self):
        return self.__name

    def serialize_to_dict(self):
        serObj = {SerializedKeys.EFFECT_NAME: self.get_effect_name()}
        return serObj


class ColorEffect(Effect):
    def __init__(self):
        Effect.__init__(self, EffectNames.COLOR_EFFECT)
        self.__color = (1.0, 1.0, 1.0, 1.0)

    def getKivyColor(self):
        return self.__color

    def setKivyColor(self, color):
        self.__color = color

    def getHexColor(self):
        hexColor = ColorTools.colorToHex(self.__color)
        return hexColor

    def serialize_to_dict(self):
        serObj = Effect.serialize_to_dict(self)
        serObj[SerializedKeys.COLOR_VALUE_HEX] = self.getHexColor()
        return serObj


class ColorTools():
    @staticmethod
    def colorToHex(color):
        color = tuple(color)
        r = ColorTools.__kivyColorToInt(color[0])
        g = ColorTools.__kivyColorToInt(color[1])
        b = ColorTools.__kivyColorToInt(color[2])
        hexColor = ("#%02x%02x%02x" % (r, g, b))
        return hexColor

    @staticmethod
    def __kivyColorToInt(value):
        return int(math.floor(255 * value))


