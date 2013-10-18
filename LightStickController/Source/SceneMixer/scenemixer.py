import json
import os
import pprint
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from Config import RGBA
from filehandler import FileHandler
from SceneMixer import SceneFrame
from serializer import Serializable
from sceneframe import ColorEffect, TextEffect
from scnconfig import EffectNames
from framehandler import FrameHandler
from playbackhandler import PlayBackHandler

Builder.load_file(os.getenv("FILE_PATH") + "/scenemixer.kv")


class SceneMixer(Widget, Serializable):
    currentTime = NumericProperty(0.0)
    sceneTime = NumericProperty(0.0)
    fadeTime = NumericProperty(0.0)
    sceneNumber = StringProperty(None)
    totalSceneTime = NumericProperty(0.0)
    bpm = NumericProperty(0.0)

    # Properties for effects
    color = ListProperty((1.0, 1.0, 1.0, 1.0))
    glowMax = NumericProperty(100.0)
    glowMin = NumericProperty(50.0)
    glowInterval = NumericProperty(0.0)

    text = StringProperty("")

    __initFinished = False

    def __init__(self, **kwargs):
        super(SceneMixer, self).__init__(**kwargs)
        self.__frameHandler = FrameHandler()

        self.__syncSceneAndFadeTime = False
        self.__globalSceneTime = False
        self.__globalFadeTime = False
        self.__loopScenes = False

        self.__dontClearEffects = True

        self.sceneTime = 0.0
        self.fadeTime = 0.0

        self.__currentFrame = None

        # init playbackHandler
        self.__isInPlayback = False
        self.__playbackHandler = PlayBackHandler(bpm=60.0, updatesPerBeat=20)
        self.__playbackHandler.addIntervalUpdateCallback(self.playbackCallbackUpdate)

        self.fileHandler = FileHandler()

        # TODO fix a better approach for checking if object is ready
        self.__initFinished = True
        self.__isInFrameChange = False

        self.syncedIsSetTest = False

    def on_bpm(self, *args):
        self.__playbackHandler.setBpm(args[1])

    def on_color(self, obj, color):
        self.__setColorEffect()

    def on_text(self, obj, text):
        self.__setTextEffect(text)

    def on_glowMax(self, obj, value):
        self.__setColorEffect()

    def on_glowMin(self, obj, value):
        self.__setColorEffect()

    def on_glowInterval(self, obj, value):
        self.__setColorEffect()

    def __beforeSetEffect(self):
        if self.__currentFrame is None:
            self.addScene()

    # COLOR EFFECT
    def __setColorEffect(self):
        if not self.__isInFrameChange:
            self.__beforeSetEffect()
            colorEffectObj = self.__currentFrame.getEffect(EffectNames.COLOR_EFFECT)
            if colorEffectObj is None:
                colorEffectObj = ColorEffect()
                self.__currentFrame.addEffect(colorEffectObj)

            colorEffectObj.setKivyColor(self.color)
            colorEffectObj.setGlowMax(self.glowMax)
            colorEffectObj.setGlowMin(self.glowMin)
            colorEffectObj.setGlowInterval(self.glowInterval)

    # TEXT EFFECT
    def __setTextEffect(self, text):
        self.__beforeSetEffect()
        textEffectObj = self.__currentFrame.getEffect(EffectNames.TEXT_EFFECT)
        if textEffectObj is None:
            textEffectObj = TextEffect()
            self.__currentFrame.addEffect(textEffectObj)

        textEffectObj.setText(text)

    def playbackCallbackUpdate(self, *args):
        self.currentTime = args[0]

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
            if not self.__isInFrameChange:
                if self.sceneTime < self.fadeTime:
                    self.fadeTime = self.sceneTime
            self.__updateSceneAndFadeTimes()

    def on_fadeTime(self, object, value):
        if self.__initFinished:
            if not self.__isInFrameChange:
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

    def toggleClearValuesOnNewScene(self, value):
        self.__dontClearEffects = value

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
            self.__isInFrameChange = True
            self.sceneTime = frame.getSceneTime()
            self.fadeTime = frame.getFadeTime()
            self.__isInFrameChange = False

        framePos = currentFrameData[FrameHandler.FRAME_POS_IDX]
        numFrames = currentFrameData[FrameHandler.FRAME_NUM_IDX]
        self.sceneNumber = ("%d:%d" % (framePos, numFrames))

        self.__setCurrentFrameEffects()
        self.totalSceneTime = self.__getTotalSceneTime()

    def __updateSceneAndFadeTimes(self):
        self.__updateCurrentFrame()

        if self.__globalFadeTime:
            self.__setGlobalFadeTime()

        if self.__globalSceneTime:
            self.__setGlobalSceneTime()

        if self.__syncSceneAndFadeTime:
            if not self.syncedIsSetTest:
                self.__setSyncedFadeAndSceneTime()
            else:
                self.syncedIsSetTest = False

        self.totalSceneTime = self.__getTotalSceneTime()

    def __updateCurrentFrame(self):
        if self.__currentFrame is not None:
            if not self.__isInFrameChange:
                self.__currentFrame.setSceneTime(self.sceneTime)
                self.__currentFrame.setFadeTime(self.fadeTime)

    def __setCurrentFrameEffects(self):
        # TODO SET TO DEFAULT VALUES IN CONFIG
        defText = str(self.text) if self.__dontClearEffects else ""
        defColor = list(self.color) if self.__dontClearEffects else RGBA(0, 0, 0)
        defMin = float(self.glowMin) if self.__dontClearEffects else 50.0
        defMax = float(self.glowMax) if self.__dontClearEffects else 100.0
        defInt = float(self.glowInterval) if self.__dontClearEffects else 0.0

        if self.__currentFrame is not None:
            # COLOR EFFECT
            # TODO SET COLOR WIDGET OFF IF NOT SET
            colorEffect = self.__currentFrame.getEffect(EffectNames.COLOR_EFFECT)
            self.__isInFrameChange = True
            self.color = colorEffect.getKivyColor() if colorEffect is not None else defColor
            self.glowMin = colorEffect.getGlowMin() if colorEffect is not None else defMin
            self.glowMax = colorEffect.getGlowMax() if colorEffect is not None else defMax
            self.glowInterval = colorEffect.getGlowInterval() if colorEffect is not None else defInt
            self.__isInFrameChange = False

            # TEXT EFFECT
            # TODO SET TEXT WIDGET OFF IF NOT SET
            textEffect = self.__currentFrame.getEffect(EffectNames.TEXT_EFFECT)
            self.text = textEffect.getText() if textEffect is not None else defText

    def __setGlobalSceneTime(self):
        self.__setSceneTimeForAllFrames(self.sceneTime)

    def __setGlobalFadeTime(self):
        self.__setFadeTimeForAllFrames(self.fadeTime)

    def __setSyncedFadeAndSceneTime(self):
        # TODO There is something going wrong here. Recursive event call bug

        self.sceneTime = self.fadeTime
        self.fadeTime = self.sceneTime

        self.syncedIsSetTest = True
        print "set synced scene fade", self.sceneTime, self.fadeTime
        self.__setFadeTimeForAllFrames(self.sceneTime)
        self.__setSceneTimeForAllFrames(self.sceneTime)

    def __setSceneTimeForAllFrames(self, sceneTime):
        self.__frameHandler.forAllFramesDo(self.__iterFuncSetSceneTime, sceneTime)

    def __setFadeTimeForAllFrames(self, fadeTime):
        self.__frameHandler.forAllFramesDo(self.__iterFuncSetFadeTime, fadeTime)

    def __getTotalSceneTime(self):
        self.totalSceneTime = 0.0
        self.__frameHandler.forAllFramesDo(self.__iterFuncCalcTotSceneTime)
        return self.totalSceneTime

    def __iterFuncSetSceneTime(self, sceneFrame, sceneTime):
        sceneFrame.setSceneTime(sceneTime)

    def __iterFuncSetFadeTime(self, sceneFrame, fadeTime):
        sceneFrame.setFadeTime(fadeTime)

    def __iterFuncCalcTotSceneTime(self, sceneFrame, *args):
        self.totalSceneTime += sceneFrame.getSceneTime()

    def serialize_to_dict(self):
        serializedDict = Serializable.serialize_to_dict(self)
        serializedDict = dict(serializedDict.items() + self.__frameHandler.serialize_to_dict().items())
        pprint.pprint(serializedDict)

        # Update property
        return serializedDict

    def deserializer_from_dict(self, showData):
        return self.__frameHandler.deserializer_from_dict(showData)
        #return Serializable.deserializer_from_dict(self, showData)

    def loadShow(self):
        popup = Popups.yesNoPopUp(titleLabel="Clear current show and load new",
                                  text="Are you sure you want to delete the current show \n"
                                       "and load a new from disk?",
                                  yesCallback=self.__loadShow)
        popup.open()

    def __loadShow(self, deleteCurrent=True, *args):
        self.fileHandler.show_load(self.__onLoadSuccessCallback)
        # TODO LOAD FROM FILE
        #currentShow = json.dumps(self.serialize_to_dict())
        if deleteCurrent:
            self.__clearCurrentShow()

    def __onLoadSuccessCallback(self, data):
        # TODO fix load from file
        self.deserializer_from_dict(json.loads(data))
        self.gotoStartOfShow()

    def saveShow(self):
        # TODO WRITE TO FILE
        show = json.dumps(self.serialize_to_dict())
        self.fileHandler.show_save(show)

    def appendShow(self):
        self.gotoEndOfShow()
        self.__loadShow(deleteCurrent=False)

    def insertShow(self):
        self.__loadShow(deleteCurrent=False)

    def clearShow(self):
        popup = Popups.yesNoPopUp(titleLabel="Clear current show",
                                  text="Are you sure you want to delete the current show?",
                                  yesCallback=self.__clearCurrentShow)
        popup.open()

    def __clearCurrentShow(self, *args):
        self.__playbackHandler.stop()
        self.__resetPlayback()
        result = (self.__frameHandler.deleteAllFrames())
        self.__setDisplayValues(result)


class Popups():
    @staticmethod
    def yesNoPopUp(titleLabel, text, yesCallback=None, noCallback=None):
        popup = Popup(title=titleLabel,
                      auto_dismiss=False,
                      size_hint=(0, 0),
                      size=(400, 200))

        mainLayout = BoxLayout(orientation="vertical")
        label = Label(text=text)
        mainLayout.add_widget(label)

        buttonLayout = BoxLayout()

        yesButton = Button(text="YES",
                           on_press=yesCallback,
                           on_release=popup.dismiss)

        noButton = Button(text="NO",
                          on_press=noCallback,
                          on_release=popup.dismiss)

        buttonLayout.add_widget(yesButton)
        buttonLayout.add_widget(noButton)

        mainLayout.add_widget(buttonLayout)

        popup.add_widget(mainLayout)
        return popup

    @staticmethod
    def errorPopup(titleLabel, text, onCloseCallback=None):
        popup = Popup(title=titleLabel,
                      auto_dismiss=False,
                      size_hint=(0, 0),
                      size=(400, 200))

        mainLayout = BoxLayout(orientation="vertical")
        label = Label(text=text, color=[1.0, 0.0, 0.0, 1.0])
        mainLayout.add_widget(label)

        okButton = Button(text="CLOSE",
                          on_press=onCloseCallback,
                          on_release=popup.dismiss)

        mainLayout.add_widget(okButton)
        popup.add_widget(mainLayout)
        return popup


class __TestScreenMixer(App):
    def build(self):
        return SceneMixer()


if __name__ == "__main__":
    test = __TestScreenMixer()
    test.run()
