import os
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.widget import Widget
from framehandler import FrameHandler

#TODO fix this import
import BpmCounter

Builder.load_file(os.getenv("FILE_PATH") + "/scenemixer.kv")


class SceneMixer(Widget):
    currentTime = NumericProperty(None)
    sceneTime = NumericProperty(None)
    fadeTime = NumericProperty(None)
    sceneNumber = StringProperty(None)

    def __init__(self, **kwargs):
        super(SceneMixer, self).__init__(**kwargs)
        self.frameHandler = FrameHandler()

        self.__syncSceneAndFadeTime = False
        self.__globalSceneTime = False
        self.__globalFadeTime = False

        self.__currentSceneTime = 0.0
        self.__currentFadeTime = 0.0

        self.__currentFrame = None

    def on_currentTime(self, object, value):
        print object, value

    def on_sceneTime(self, object, value):
        print object, value

    def on_fadeTime(self, object, value):
        print object, value

    def on_sceneNumber(self, object, value):
        print object, value

    def addScene(self):
        self.__setDisplayValues(self.frameHandler.addFrameAtEnd())

    def insertSceneBefore(self):
        self.__setDisplayValues(self.frameHandler.insertFrameBeforePointer())

    def insertSceneAfter(self):
        self.__setDisplayValues(self.frameHandler.insertFrameAfterPointer())

    def deleteScene(self):
        self.__setDisplayValues(self.frameHandler.deleteCurrentFrame())

    def startStopPlayback(self, *args):
        #TODO
        print args, "startStop scene"

    def gotoStartOfShow(self):
        self.__setDisplayValues(self.frameHandler.moveFramePointerToStart())

    def gotoEndOfShow(self):
        self.__setDisplayValues(self.frameHandler.moveFramePointerToEnd())

    def gotoPrevScene(self):
        self.__setDisplayValues(self.frameHandler.moveFramePointerDown())

    def gotoNextScene(self):
        self.__setDisplayValues(self.frameHandler.moveFramePointerUp())

    def toggleSyncSceneAndFadeTime(self, value):
        #TODO
        print "SYNC SCENE AND FADE TIME", value

    def toggleGlobalSceneTime(self, value):
        #TODO
        print "Set global scene time", value

    def toggleGlobalFadeTime(self, value):
        #TODO
        print "Set global fade time ", value

    def toggleLoopScenes(self, value):
        #TODO
        print "Set loop after end ", value

    def __setDisplayValues(self, currentFrame):
        frame = currentFrame[FrameHandler.FRAME_OBJ_IDX]
        self.__currentFrame = frame
        if frame is not None:
            self.sceneTime = frame.getSceneTime()
            self.fadeTime = frame.getFadeTime()
        self.sceneNumber = currentFrame[FrameHandler.FRAME_POS_IDX]


class __TestScreenMixer(App):
    def build(self):
        return SceneMixer()

if __name__ == "__main__":
    test = __TestScreenMixer()
    test.run()