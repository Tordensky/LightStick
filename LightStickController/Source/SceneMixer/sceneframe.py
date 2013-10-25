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
        if self.__fadeTime > self.__sceneTime:
            self.__sceneTime = float(self.__fadeTime)
        self.__fadeTime = float(fadeTime)

    def getSceneTime(self):
        return self.__sceneTime

    def setSceneTime(self, sceneTime):
        self.__sceneTime = float(sceneTime)

    def serialize_to_dict(self):
        serDict = Serializable.serialize_to_dict(self)
        serDict[SerializedKeys.FADE_TIME] = self.__fadeTime
        serDict[SerializedKeys.SCENE_TIME] = self.__sceneTime

        serDict[SerializedKeys.EFFECT_LIST] = []
        for effect in self.getEffects():
            serDict[SerializedKeys.EFFECT_LIST].append(effect.serialize_to_dict())

        return serDict

    def deserializer_from_dict(self, showDict):
        self.__sceneTime = showDict[SerializedKeys.SCENE_TIME]
        self.__fadeTime = showDict[SerializedKeys.FADE_TIME]

        if SerializedKeys.EFFECT_LIST in showDict:
            for effect in showDict[SerializedKeys.EFFECT_LIST]:
                if effect[SerializedKeys.EFFECT_NAME] == EffectNames.COLOR_EFFECT:
                    colorEffect = ColorEffect()
                    colorEffect.deserializer_from_dict(effect)
                    self.addEffect(colorEffect)

                elif effect[SerializedKeys.EFFECT_NAME] == EffectNames.TEXT_EFFECT:
                    textEffect = TextEffect()
                    textEffect.deserializer_from_dict(effect)
                    self.addEffect(textEffect)


class Effect(Serializable):
    def __init__(self, name):
        self.__name = name

    def get_effect_name(self):
        return self.__name

    def serialize_to_dict(self):
        serObj = {SerializedKeys.EFFECT_NAME: self.get_effect_name()}
        return serObj


class TextEffect(Effect):
    def __init__(self):
        Effect.__init__(self, EffectNames.TEXT_EFFECT)
        self.__text = ""

    def setText(self, text):
        self.__text = text

    def getText(self):
        return self.__text

    def serialize_to_dict(self):
        serObj = Effect.serialize_to_dict(self)
        serObj[SerializedKeys.TEXT_VALUE_KEY] = self.getText()
        return serObj

    def deserializer_from_dict(self, showDict):
        self.setText(showDict[SerializedKeys.TEXT_VALUE_KEY])


class ColorEffect(Effect):
    def __init__(self):
        Effect.__init__(self, EffectNames.COLOR_EFFECT)
        self.__color = (1.0, 1.0, 1.0, 1.0)

        self.__glowMax = 1.0
        self.__glowMin = 0.0
        self.__glowInterval = 0.0
        self.__glowOffset = False

    def setGlowMin(self, value):
        self.__glowMin = value

    def setGlowMax(self, value):
        self.__glowMax = value

    def setGlowInterval(self, value):
        self.__glowInterval = value

    def setGlowOffset(self, value):
        self.__glowOffset = value

    def getGlowMin(self):
        return self.__glowMin

    def getGlowMax(self):
        return self.__glowMax

    def getGlowInterval(self):
        return self.__glowInterval

    def getGlowOffset(self):
        return self.__glowOffset

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

        serObj[SerializedKeys.GLOW_MAX] = self.getGlowMax() / 100.0
        serObj[SerializedKeys.GLOW_MIN] = self.getGlowMin() / 100.0
        serObj[SerializedKeys.GLOW_INTERVAL] = self.getGlowInterval()
        serObj[SerializedKeys.GLOW_OFFSET] = self.getGlowOffset()
        return serObj

    def deserializer_from_dict(self, showDict):
        self.setColorFromHEX(showDict[SerializedKeys.COLOR_VALUE_HEX])
        self.setGlowMax(float(showDict[SerializedKeys.GLOW_MAX]) * 100.0)
        self.setGlowMin(float(showDict[SerializedKeys.GLOW_MIN]) * 100.0)
        self.setGlowInterval(showDict[SerializedKeys.GLOW_INTERVAL])

        # ADDING BACKWARD COMPATIBILITY FOR HANDLING OLD SHOW FILES
        if SerializedKeys.GLOW_INTERVAL in showDict:
            self.setGlowOffset(showDict[SerializedKeys.GLOW_INTERVAL])

    def setColorFromHEX(self, hexColor):
        self.__color = ColorTools.hexTokivy(hexColor)


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
    def hexTokivy(hexValue):
        r = float(int(hexValue[1:3], 16) / 255.0)
        g = float(int(hexValue[3:5], 16) / 255.0)
        b = float(int(hexValue[5:7], 16) / 255.0)
        return [r, g, b, 1.0]

    @staticmethod
    def __kivyColorToInt(value):
        return int(math.floor(255 * value))
