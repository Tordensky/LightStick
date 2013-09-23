import os
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.widget import Widget
from SceneMixer import SceneFrame
from framehandler import FrameHandler
from playbackhandler import PlayBackHandler

#TODO fix this import
import BpmCounter

Builder.load_file(os.getenv("FILE_PATH") + "/scenemixer.kv")


class SceneMixer(Widget):
    currentTime = NumericProperty(0.0)
    sceneTime = NumericProperty(0.0)
    fadeTime = NumericProperty(0.0)
    sceneNumber = StringProperty(None)

    __initFinished = False

    def __init__(self, **kwargs):
        super(SceneMixer, self).__init__(**kwargs)
        self.__frameHandler = FrameHandler()

        self.__syncSceneAndFadeTime = False
        self.__globalSceneTime = False
        self.__globalFadeTime = False
        self.__loopScenes = False

        self.sceneTime = 0.0
        self.fadeTime = 0.0

        self.__currentFrame = None

        # init playbackHandler
        self.__isInPlayback = False
        self.__playbackHandler = PlayBackHandler(bpm=60.0, updatesPerBeat=20)
        self.__playbackHandler.addIntervalUpdateCallback(self.playbackCallbackUpdate)

        # TODO fix a better approach for checking if object is ready
        self.__initFinished = True

    def playbackCallbackUpdate(self, *args):
        self.currentTime = round(args[0], 1)
        if self.currentTime >= self.sceneTime:
            self.__playbackHandler.reset()
            self.gotoNextScene()
        # TODO if not loop and last scene end or restart

    def on_sceneTime(self, object, value):
        if self.__initFinished:
            if self.sceneTime < self.fadeTime:
                self.fadeTime = self.sceneTime
            self.__updateSceneAndFadeTimes()

    def on_fadeTime(self, object, value):
        if self.__initFinished:
            if self.fadeTime > self.sceneTime:
                self.sceneTime = self.fadeTime
            self.__updateSceneAndFadeTimes()

    def addScene(self):
        sceneFrame = self.__createNewScene()
        self.__setDisplayValues(self.__frameHandler.addFrameAtEnd(sceneFrame))

    def insertSceneBefore(self):
        sceneFrame = self.__createNewScene()
        self.__setDisplayValues(self.__frameHandler.insertFrameBeforePointer(sceneFrame))

    def insertSceneAfter(self):
        sceneFrame = self.__createNewScene()
        self.__setDisplayValues(self.__frameHandler.insertFrameAfterPointer(sceneFrame))

    def __createNewScene(self):
        sceneFrame = SceneFrame()
        sceneFrame.setSceneTime(self.sceneTime)
        sceneFrame.setFadeTime(self.fadeTime)
        return sceneFrame

    def startStopPlayback(self, *args):
        self.__isInPlayback = not self.__isInPlayback
        if self.__isInPlayback:
            self.__playbackHandler.start()
        else:
            self.__playbackHandler.stop()

    def deleteScene(self):
        self.__setDisplayValues(self.__frameHandler.deleteCurrentFrame())

    def gotoStartOfShow(self):
        self.__resetPlayback()
        self.__setDisplayValues(self.__frameHandler.moveFramePointerToStart())

    def __resetPlayback(self):
        self.currentTime = 0.0
        self.__playbackHandler.reset()

    def gotoEndOfShow(self):
        self.__resetPlayback()
        self.__setDisplayValues(self.__frameHandler.moveFramePointerToEnd())

    def gotoPrevScene(self):
        self.__resetPlayback()
        self.__setDisplayValues(self.__frameHandler.moveFramePointerDown())

    def gotoNextScene(self):
        self.__resetPlayback()
        self.__setDisplayValues(self.__frameHandler.moveFramePointerUp())

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

    def __setDisplayValues(self, currentFrame):
        frame = currentFrame[FrameHandler.FRAME_OBJ_IDX]
        self.__currentFrame = frame
        if frame is not None:
            self.sceneTime = frame.getSceneTime()
            self.fadeTime = frame.getFadeTime()

        framePos = currentFrame[FrameHandler.FRAME_POS_IDX]
        numFrames = currentFrame[FrameHandler.FRAME_NUM_IDX]
        self.sceneNumber = ("%d:%d" % (framePos, numFrames))

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
            self.__currentFrame.setSceneTime(self.sceneTime)
            self.__currentFrame.setFadeTime(self.fadeTime)

    def __setGlobalSceneTime(self):
        self.__setSceneTimeForAllFrames(self.sceneTime)

    def __setGlobalFadeTime(self):
        self.__setFadeTimeForAllFrames(self.fadeTime)

    def __setSyncedFadeAndSceneTime(self):
        self.fadeTime = self.sceneTime

        self.__setFadeTimeForAllFrames(self.fadeTime)
        self.__setSceneTimeForAllFrames(self.sceneTime)

    def __setSceneTimeForAllFrames(self, sceneTime):
        self.__frameHandler.forAllFramesDo(self.iterFuncSetSceneTime, sceneTime)

    def __setFadeTimeForAllFrames(self, fadeTime):
        self.__frameHandler.forAllFramesDo(self.iterFuncSetFadeTime, fadeTime)

    def iterFuncSetSceneTime(self, sceneFrame, sceneTime):
        sceneFrame.setSceneTime(sceneTime)

    def iterFuncSetFadeTime(self, sceneFrame, fadeTime):
        sceneFrame.setFadeTime(fadeTime)


class __TestScreenMixer(App):
    def build(self):
        return SceneMixer()

if __name__ == "__main__":
    test = __TestScreenMixer()
    test.run()
