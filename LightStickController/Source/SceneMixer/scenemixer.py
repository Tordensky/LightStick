import os
import pprint
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, ListProperty, DictProperty
from kivy.uix.widget import Widget
from SceneMixer import SceneFrame
from serializer import Serializable
from sceneframe import ColorEffect
from scnconfig import EffectNames
from framehandler import FrameHandler
from playbackhandler import PlayBackHandler

Builder.load_file(os.getenv("FILE_PATH") + "/scenemixer.kv")


class SceneMixer(Widget, Serializable):
    currentTime = NumericProperty(0.0)
    sceneTime = NumericProperty(0.0)
    fadeTime = NumericProperty(0.0)
    sceneNumber = StringProperty(None)
    bpm = NumericProperty(0.0)

    # Properties for effects
    color = ListProperty((1.0, 1.0, 1.0, 1.0))

    __initFinished = False

    def __init__(self, **kwargs):
        super(SceneMixer, self).__init__(**kwargs)
        self.__frameHandler = FrameHandler()

        self.__syncSceneAndFadeTime = False
        self.__globalSceneTime = False
        self.__globalFadeTime = False
        self.__loopScenes = True

        self.sceneTime = 0.0
        self.fadeTime = 0.0

        self.__currentFrame = None

        # init playbackHandler
        self.__isInPlayback = False
        self.__playbackHandler = PlayBackHandler(bpm=60.0, updatesPerBeat=20)
        self.__playbackHandler.addIntervalUpdateCallback(self.playbackCallbackUpdate)

        # TODO fix a better approach for checking if object is ready
        self.__initFinished = True
        self.isInFrameChange = False

    def on_bpm(self, *args):
        self.__playbackHandler.setBpm(args[1])

    def on_color(self, obj, color):
        self.__setColorEffect(color)

    def __beforeSetEffect(self):
        if self.__currentFrame is None:
            self.addScene()

    def __setColorEffect(self, color):
        self.__beforeSetEffect()
        colorEffectObj = self.__currentFrame.getEffect(EffectNames.COLOR_EFFECT)
        if colorEffectObj is None:
            colorEffectObj = ColorEffect()
            self.__currentFrame.addEffect(colorEffectObj)

        colorEffectObj.setKivyColor(color)

    def playbackCallbackUpdate(self, *args):
        self.currentTime = round(args[0], 1)

        if self.currentTime >= self.sceneTime:
            atEnd = self.__frameHandler.isAtEndOfFrames()
            self.__playbackHandler.reset()
            if atEnd and self.__loopScenes:
                self.gotoStartOfShow()
            elif atEnd:
                self.startStopPlayback()
            else:
                self.gotoNextScene()

    def on_sceneTime(self, object, value):
        if self.__initFinished:
            if not self.isInFrameChange:
                if self.sceneTime < self.fadeTime:
                    self.fadeTime = self.sceneTime
            self.__updateSceneAndFadeTimes()

    def on_fadeTime(self, object, value):
        if self.__initFinished:
            if not self.isInFrameChange:
                if self.fadeTime > self.sceneTime:
                    self.sceneTime = self.fadeTime
            self.__updateSceneAndFadeTimes()

    def addScene(self):
        self.__before_create_scene()

        sceneFrame = self.__createNewScene()
        result = (self.__frameHandler.addFrameAtEnd(sceneFrame))
        self.__setDisplayValues(result)
        return result

    def insertSceneBefore(self):
        self.__before_create_scene()

        sceneFrame = self.__createNewScene()
        result = (self.__frameHandler.insertFrameBeforePointer(sceneFrame))
        self.__setDisplayValues(result)
        return result

    def insertSceneAfter(self):
        self.__before_create_scene()

        sceneFrame = self.__createNewScene()
        result = (self.__frameHandler.insertFrameAfterPointer(sceneFrame))
        self.__setDisplayValues(result)
        return result

    def __before_create_scene(self):
        if self.sceneTime == 0.0:
            self.sceneTime = 1.0

    def __createNewScene(self):
        sceneFrame = SceneFrame()
        sceneFrame.setSceneTime(self.sceneTime)
        sceneFrame.setFadeTime(self.fadeTime)
        return sceneFrame

    def startStopPlayback(self, *args):
        self.__isInPlayback = not self.__isInPlayback
        if self.__isInPlayback:
            self.__resetPlayback()
            self.__playbackHandler.start()
        else:
            self.__playbackHandler.stop()
            self.__resetPlayback()

    def deleteScene(self):
        result = (self.__frameHandler.deleteCurrentFrame())
        self.__setDisplayValues(result)
        return result

    def gotoStartOfShow(self):
        self.__resetPlayback()
        result = (self.__frameHandler.moveFramePointerToStart())
        self.__setDisplayValues(result)
        return result

    def __resetPlayback(self):
        self.currentTime = 0.0
        self.__playbackHandler.reset()

    def gotoEndOfShow(self):
        self.__resetPlayback()
        result = (self.__frameHandler.moveFramePointerToEnd())
        self.__setDisplayValues(result)
        return result

    def gotoPrevScene(self):
        self.__resetPlayback()
        result = (self.__frameHandler.moveFramePointerDown())
        self.__setDisplayValues(result)
        return result

    def gotoNextScene(self):
        self.__resetPlayback()
        result = (self.__frameHandler.moveFramePointerUp())
        self.__setDisplayValues(result)
        return result

    def toggleSyncSceneAndFadeTime(self, value):
        self.__syncSceneAndFadeTime = value
        self.__updateSceneAndFadeTimes()

    def toggleGlobalSceneTime(self, value):
        self.__globalSceneTime = value
        self.__updateSceneAndFadeTimes()

    def toggleGlobalFadeTime(self, value):
        self.__globalFadeTime = value
        self.__updateSceneAndFadeTimes()

    def toggleLoopScenes(self, value):
        self.__loopScenes = value

    # TODO RENAME OR REFACTOR
    def __setDisplayValues(self, currentFrameData):
        frame = currentFrameData[FrameHandler.FRAME_OBJ_IDX]
        self.__currentFrame = frame
        if frame is not None:
            self.isInFrameChange = True
            self.sceneTime = frame.getSceneTime()
            self.fadeTime = frame.getFadeTime()
            self.isInFrameChange = False

        framePos = currentFrameData[FrameHandler.FRAME_POS_IDX]
        numFrames = currentFrameData[FrameHandler.FRAME_NUM_IDX]
        self.sceneNumber = ("%d:%d" % (framePos, numFrames))

        self.__setCurrentFrameEffects()

    def __updateSceneAndFadeTimes(self):
        self.__updateCurrentFrame()

        if self.__globalFadeTime:
            self.__setGlobalFadeTime()

        if self.__globalSceneTime:
            self.__setGlobalSceneTime()

        if self.__syncSceneAndFadeTime:
            self.__setSyncedFadeAndSceneTime()

    def __updateCurrentFrame(self):
        if self.__currentFrame is not None:
            if not self.isInFrameChange:
                self.__currentFrame.setSceneTime(self.sceneTime)
                self.__currentFrame.setFadeTime(self.fadeTime)

    def __setCurrentFrameEffects(self):
        if self.__currentFrame is not None:
            effects = self.__currentFrame.getEffects()
            for effect in effects:
                if effect.get_effect_name() == EffectNames.COLOR_EFFECT:
                    self.color = effect.getKivyColor()

    def __setGlobalSceneTime(self):
        self.__setSceneTimeForAllFrames(self.sceneTime)

    def __setGlobalFadeTime(self):
        self.__setFadeTimeForAllFrames(self.fadeTime)

    def __setSyncedFadeAndSceneTime(self):
        # TODO There is something going wrong here. Recursive event call bug
        self.fadeTime = self.sceneTime

        self.__setFadeTimeForAllFrames(self.fadeTime)
        self.__setSceneTimeForAllFrames(self.sceneTime)

    def __setSceneTimeForAllFrames(self, sceneTime):
        self.__frameHandler.forAllFramesDo(self.__iterFuncSetSceneTime, sceneTime)

    def __setFadeTimeForAllFrames(self, fadeTime):
        self.__frameHandler.forAllFramesDo(self.__iterFuncSetFadeTime, fadeTime)

    def __iterFuncSetSceneTime(self, sceneFrame, sceneTime):
        sceneFrame.setSceneTime(sceneTime)

    def __iterFuncSetFadeTime(self, sceneFrame, fadeTime):
        sceneFrame.setFadeTime(fadeTime)

    def serialize_to_dict(self):
        serializedDict = Serializable.serialize_to_dict(self)
        serializedDict = dict(serializedDict.items() + self.__frameHandler.serialize_to_dict().items())
        pprint.pprint(serializedDict)

        # Update property
        return serializedDict


class __TestScreenMixer(App):
    def build(self):
        return SceneMixer()

if __name__ == "__main__":
    test = __TestScreenMixer()
    test.run()
