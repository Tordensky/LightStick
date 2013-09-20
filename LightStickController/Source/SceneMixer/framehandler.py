from sceneframe import SceneFrame


class FrameHandler():
    SCENE_TIME_IDX = 0
    FADE_TIME_IDX = 1
    SCENE_NUMBER_IDX = 2

    def __init__(self):
        self.__framePointer = 0
        self.__frames = []

        self.__syncSceneAndFadeTime = False
        self.__globalSceneTime = False
        self.__globalFadeTime = False

        self.__currentSceneTime = 0.0
        self.__currentFadeTime = 0.0

    def getCurrentFrame(self):
        index = self.__getCurrentListIndex()
        if index is not None:
            return self.__frames[index]
        return None

    def addFrameAtEnd(self):
        newFrame = self.__createNewFrame()
        self.__frames.append(newFrame)
        self.moveFramePointerToEnd()
        return self.__getCurrentSceneInfo()

    def insertFrameBeforePointer(self):
        newFrame = self.__createNewFrame()
        index = self.__getCurrentListIndex()
        if index is not None:
            self.__frames.insert(index, newFrame)
        else:
            self.__frames.append(newFrame)
            self.moveFramePointerToEnd()
        return self.__getCurrentSceneInfo()

    def insertFrameAfterPointer(self):
        newFrame = SceneFrame()
        index = self.__getCurrentListIndex()
        if index is not None:
            self.__frames.insert(index + 1, newFrame)
            self.moveFramePointerUp()
        else:
            self.__frames.append(newFrame)
            self.moveFramePointerToEnd()
        return self.__getCurrentSceneInfo()

    def deleteCurrentFrame(self):
        index = self.__getCurrentListIndex()
        if index is not None:
            self.__frames.pop(index)
            self.moveFramePointerDown()
        return self.__getCurrentSceneInfo()

    def moveFramePointerUp(self):
        if self.__framePointer < self.__numFrames():
            self.__framePointer += 1
        return self.__getCurrentSceneInfo()

    def moveFramePointerDown(self):
        if self.__framePointer > 1:
            self.__framePointer -= 1
        elif self.__numFrames() == 0:
            self.__framePointer = 0
        return self.__getCurrentSceneInfo()

    def moveFramePointerToStart(self):
        if self.__numFrames() > 0:
            self.__framePointer = 1
        return self.__getCurrentSceneInfo()

    def moveFramePointerToEnd(self):
        self.__framePointer = len(self.__frames)
        return self.__getCurrentSceneInfo()

    def __numFrames(self):
        return len(self.__frames)

    def __createNewFrame(self):
        frame = SceneFrame()
        return frame

    def __getCurrentListIndex(self):
        if self.__framePointer > 0:
            return self.__framePointer - 1
        return None

    def __getCurrentSceneInfo(self):
        frame = self.getCurrentFrame()

        sceneTime = 0.0
        fadeTime = 0.0
        if frame is not None:
            sceneTime = frame.getSceneTime()
            fadeTime = frame.getFadeTime()

        sceneNumberStr = str("%d:%d" % (self.__framePointer, self.__numFrames()))

        return sceneTime, fadeTime, sceneNumberStr

