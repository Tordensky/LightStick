from kivy.clock import Clock


class PlayBackHandler():
    def __init__(self, bpm=0.0, updatesPerBeat=20.0):
        self.__bpm = float(bpm)
        self.__updatesPerBeat = float(updatesPerBeat)

        self.__updateInterval = self.__getIntervalTime()

        self.__currTime = 0.0
        self.__lastTime = 0.0

        self.__callbacks = []

    def setBpm(self, bpm):
        self.__bpm = bpm
        self.__updateInterval = self.__getIntervalTime()

    def addIntervalUpdateCallback(self, callback):
        self.__callbacks.append(callback)

    def start(self):
        self.__updateInterval = self.__getIntervalTime()
        self.__scheduleNextUpdate()

    def stop(self):
        Clock.unschedule(self.__onUpdate)
        self.__updateInterval = 0.0

    def stopAndReset(self):
        self.stop()
        self.reset()

    def reset(self):
        self.__currTime = 0.0

    def __getIntervalTime(self):
        if self.__bpm:
            return (1.0 / (float(self.__bpm) / 60.0)) / float(self.__updatesPerBeat)
        return 0.0

    def __scheduleNextUpdate(self):
        Clock.unschedule(self.__onUpdate)
        if self.__updateInterval:
            Clock.schedule_once(self.__onUpdate, self.__updateInterval)

    def __onUpdate(self, *args):
        self.__currTime += 1.0 / self.__updatesPerBeat
        for callback in self.__callbacks:
            callback(self.__currTime)

        self.__scheduleNextUpdate()
