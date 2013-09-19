from sceneframe import SceneFrame


class FrameHandler():
    def __init__(self):
        self._framePointer = 0
        self._frames = []

    def numFrames(self):
        return len(self._frames)

    def addFrameAtEnd(self):
        newFrame = SceneFrame()
        self._frames.append(newFrame)

    def moveFramePointerUp(self):
        if self._framePointer < self.numFrames():
            self._framePointer += 1

    def moveFramePointerDown(self):
        if self._framePointer > 0:
            self._framePointer -= 1


if __name__ == "__main__":
    frameHandler = FrameHandler()
    print "num frames should be zero after init:", frameHandler.numFrames()

    frameHandler.addFrameAtEnd()
    print "num frames should be one after add:", frameHandler.numFrames()
