import os
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.widget import Widget
from SceneMixer import SceneFrame
from framehandler import FrameHandler

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
        self.frameHandler = FrameHandler()

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
        self.__playbackHandler.setIntervalUpdateCallback(self.playbackCallbackUpdate)

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
            self.updateSceneAndFadeTimes()

    def on_fadeTime(self, object, value):
        if self.__initFinished:
            if self.fadeTime > self.sceneTime:
                self.sceneTime = self.fadeTime
            self.updateSceneAndFadeTimes()

    def addScene(self):
        sceneFrame = self.__createNewScene()
        self.__setDisplayValues(self.frameHandler.addFrameAtEnd(sceneFrame))

    def insertSceneBefore(self):
        sceneFrame = self.__createNewScene()
        self.__setDisplayValues(self.frameHandler.insertFrameBeforePointer(sceneFrame))

    def insertSceneAfter(self):
        sceneFrame = self.__createNewScene()
        self.__setDisplayValues(self.frameHandler.insertFrameAfterPointer(sceneFrame))

    def __createNewScene(self):
        sceneFrame = SceneFrame()
        sceneFrame.setSceneTime(self.sceneTime)
        sceneFrame.setFadeTime(self.fadeTime)
        return sceneFrame

    def deleteScene(self):
        self.__setDisplayValues(self.frameHandler.deleteCurrentFrame())

    def startStopPlayback(self, *args):
        self.__isInPlayback = not self.__isInPlayback
        if self.__isInPlayback:
            self.__playbackHandler.start()
        else:
            self.__playbackHandler.stop()

    def __resetPlayback(self):
        self.currentTime = 0.0
        self.__playbackHandler.reset()

    def gotoStartOfShow(self):
        self.__resetPlayback()
        self.__setDisplayValues(self.frameHandler.moveFramePointerToStart())

    def gotoEndOfShow(self):
        self.__resetPlayback()
        self.__setDisplayValues(self.frameHandler.moveFramePointerToEnd())

    def gotoPrevScene(self):
        self.__resetPlayback()
        self.__setDisplayValues(self.frameHandler.moveFramePointerDown())

    def gotoNextScene(self):
        self.__resetPlayback()
        self.__setDisplayValues(self.frameHandler.moveFramePointerUp())

    def toggleSyncSceneAndFadeTime(self, value):
        self.__syncSceneAndFadeTime = value
        self.updateSceneAndFadeTimes()

    def toggleGlobalSceneTime(self, value):
        self.__globalSceneTime = value
        self.updateSceneAndFadeTimes()

    def toggleGlobalFadeTime(self, value):
        self.__globalFadeTime = value
        self.updateSceneAndFadeTimes()

    def toggleLoopScenes(self, value):
        self.__loopScenes = value

    def __setDisplayValues(self, currentFrame):
        frame = currentFrame[FrameHandler.FRAME_OBJ_IDX]
        self.__currentFrame = frame
        if frame is not None:
            self.sceneTime = frame.getSceneTime()
            self.fadeTime = frame.getFadeTime()
        self.sceneNumber = currentFrame[FrameHandler.FRAME_POS_IDX]

    def updateSceneAndFadeTimes(self):
        self.__updateCurrentFrame()

        if self.__globalFadeTime:
            self.setGlobalFadeTime()

        if self.__globalSceneTime:
            self.setGlobalSceneTime()

        if self.__syncSceneAndFadeTime:
            self.setSyncFadeAndSceneTime()

    def __updateCurrentFrame(self):
        if self.__currentFrame is not None:
            self.__currentFrame.setSceneTime(self.sceneTime)
            self.__currentFrame.setFadeTime(self.fadeTime)

    def setGlobalSceneTime(self):
        self.__setSceneTimeForAllFrames(self.sceneTime)

    def setGlobalFadeTime(self):
        self.__setFadeTimeForAllFrames(self.fadeTime)

    def setSyncFadeAndSceneTime(self):
        self.fadeTime = self.sceneTime

        self.__setFadeTimeForAllFrames(self.fadeTime)
        self.__setSceneTimeForAllFrames(self.sceneTime)

    def __setSceneTimeForAllFrames(self, sceneTime):
        self.frameHandler.forAllFramesDo(self.iterFuncSetSceneTime, sceneTime)

    def __setFadeTimeForAllFrames(self, fadeTime):
        self.frameHandler.forAllFramesDo(self.iterFuncSetFadeTime, fadeTime)

    def iterFuncSetSceneTime(self, sceneFrame, sceneTime):
        sceneFrame.setSceneTime(sceneTime)

    def iterFuncSetFadeTime(self, sceneFrame, fadeTime):
        sceneFrame.setFadeTime(fadeTime)


class PlayBackHandler():
    def __init__(self, bpm=0, updatesPerBeat=100.0):
        self.__pbm = bpm
        self.__bpmUpdateInterval = 1.0 / float(updatesPerBeat)

        self.__currTime = 0.0
        self.__callback = None

    def setIntervalUpdateCallback(self, callback):
        self.__callback = callback

    def start(self):
        interval = self.__getIntervalTime()
        Clock.schedule_interval(self.__update, interval)

    def stop(self):
        Clock.unschedule(self.__update)

    def reset(self):
        self.__currTime = 0.0

    def __getIntervalTime(self):
        return 60.0 * self.__bpmUpdateInterval / self.__pbm

    def __update(self, *args):
        self.__currTime += self.__bpmUpdateInterval
        self.__callback(self.__currTime)


class __TestScreenMixer(App):
    def build(self):
        return SceneMixer()

if __name__ == "__main__":
    test = __TestScreenMixer()
    test.run()
