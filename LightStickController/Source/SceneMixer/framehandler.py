from collections import namedtuple
from sceneframe import SceneFrame


class FrameHandler():
    FRAME_OBJ_IDX = 0
    FRAME_POS_IDX = 1
    FRAME_NUM_IDX = 2

    def __init__(self):
        self.__framePointer = 0
        self.__frames = []

    def getCurrentFrame(self):
        index = self.__getCurrentListIndex()
        if index is not None:
            return self.__frames[index]
        return None

    def addFrameAtEnd(self, newFrame):
        self.__frames.append(newFrame)
        self.moveFramePointerToEnd()
        return self.__getCurrentFrameWithInfo()

    def insertFrameBeforePointer(self, newFrame):
        index = self.__getCurrentListIndex()
        if index is not None:
            self.__frames.insert(index, newFrame)
        else:
            self.__frames.append(newFrame)
            self.moveFramePointerToEnd()
        return self.__getCurrentFrameWithInfo()

    def insertFrameAfterPointer(self, newFrame):
        index = self.__getCurrentListIndex()
        offset = 1
        if index is not None:
            self.__frames.insert(index + offset, newFrame)
            self.moveFramePointerUp()
        else:
            self.__frames.append(newFrame)
            self.moveFramePointerToEnd()
        return self.__getCurrentFrameWithInfo()

    def deleteCurrentFrame(self):
        index = self.__getCurrentListIndex()
        if index is not None:
            self.__frames.pop(index)
            self.moveFramePointerDown()
        return self.__getCurrentFrameWithInfo()

    def moveFramePointerUp(self):
        if self.__framePointer < self.__numFrames():
            self.__framePointer += 1
        return self.__getCurrentFrameWithInfo()

    def moveFramePointerDown(self):
        if self.__framePointer > 1:
            self.__framePointer -= 1
        elif self.__numFrames() == 0:
            self.__framePointer = 0
        return self.__getCurrentFrameWithInfo()

    def moveFramePointerToStart(self):
        if self.__numFrames() > 0:
            self.__framePointer = 1
        return self.__getCurrentFrameWithInfo()

    def moveFramePointerToEnd(self):
        self.__framePointer = len(self.__frames)
        return self.__getCurrentFrameWithInfo()

    def forAllFramesDo(self, action, *args):
        for frame in self.__frames:
            action(frame, *args)

    def __numFrames(self):
        return len(self.__frames)

    def __getCurrentListIndex(self):
        if self.__framePointer > 0:
            return self.__framePointer - 1
        return None

    def __getCurrentFrameWithInfo(self):
        FrameHolder = namedtuple("Frame", ["FrameObject", "FramePos", "NumFrames"])
        frame = self.getCurrentFrame()

        framePos = self.__framePointer
        numFrames = self.__numFrames()

        currentFrame = FrameHolder(frame, framePos, numFrames)
        return currentFrame
