from collections import namedtuple
from sceneframe import SceneFrame
from scnconfig import SerializedKeys
from serializer import Serializable


class FrameHandler(Serializable):
    FRAME_OBJ_IDX = 0
    FRAME_POS_IDX = 1
    FRAME_NUM_IDX = 2

    def __init__(self):
        self._framePointer = 0
        self._frames = []

    def _getCurrentFrame(self):
        index = self._getCurrentListIndex()
        if index is not None:
            return self._frames[index]
        return None

    def addFrameAtEnd(self, newFrame):
        self._frames.append(newFrame)
        self.moveFramePointerToEnd()
        return self._getCurrentFrameWithInfo()

    def insertFrameBeforePointer(self, newFrame):
        index = self._getCurrentListIndex()
        if index is not None:
            self._frames.insert(index, newFrame)
        else:
            self._frames.append(newFrame)
            self.moveFramePointerToEnd()
        return self._getCurrentFrameWithInfo()

    def insertFrameAfterPointer(self, newFrame):
        index = self._getCurrentListIndex()
        offset = 1
        if index is not None:
            self._frames.insert(index + offset, newFrame)
            self.moveFramePointerUp()
        else:
            self._frames.append(newFrame)
            self.moveFramePointerToEnd()
        return self._getCurrentFrameWithInfo()

    def deleteCurrentFrame(self):
        index = self._getCurrentListIndex()
        if index is not None:
            self._frames.pop(index)
            self.moveFramePointerDown()
        return self._getCurrentFrameWithInfo()

    def deleteAllFrames(self):
        del self._frames
        self._frames = []
        self._framePointer = 0
        return self._getCurrentFrameWithInfo()

    def moveFramePointerUp(self):
        if self._framePointer < self._numFrames():
            self._framePointer += 1
        return self._getCurrentFrameWithInfo()

    def moveFramePointerDown(self):
        if self._framePointer > 1:
            self._framePointer -= 1
        elif self._numFrames() == 0:
            self._framePointer = 0
        return self._getCurrentFrameWithInfo()

    def moveFramePointerToStart(self):
        if self._numFrames() > 0:
            self._framePointer = 1
        return self._getCurrentFrameWithInfo()

    def moveFramePointerToEnd(self):
        self._framePointer = len(self._frames)
        return self._getCurrentFrameWithInfo()

    def forAllFramesDo(self, action, *args):
        for frame in self._frames:
            action(frame, *args)

    def _numFrames(self):
        return len(self._frames)

    def _getCurrentListIndex(self):
        if self._framePointer > 0:
            return self._framePointer - 1
        return None

    def _getCurrentFrameWithInfo(self):
        FrameHolder = namedtuple("Frame", ["FrameObject", "FramePos", "NumFrames"])
        frame = self._getCurrentFrame()

        framePos = self._framePointer
        numFrames = self._numFrames()

        currentFrame = FrameHolder(frame, framePos, numFrames)
        return currentFrame

    def isAtEndOfFrames(self):
        return self._framePointer == self._numFrames()

    def serialize_to_dict(self):
        serializedDict = Serializable.serialize_to_dict(self)
        serializedFramesList = []

        for frame in self._frames:
            frameDict = frame.serialize_to_dict()
            serializedFramesList.append(frameDict)
        serializedDict[SerializedKeys.FRAME_LIST] = serializedFramesList

        return serializedDict

    def deserializer_from_dict(self, showDict):
        if SerializedKeys.FRAME_LIST in showDict:
            for sceneInfo in showDict[SerializedKeys.FRAME_LIST]:
                tmpScene = SceneFrame()
                tmpScene.deserializer_from_dict(sceneInfo)
                self.insertFrameAfterPointer(tmpScene)
