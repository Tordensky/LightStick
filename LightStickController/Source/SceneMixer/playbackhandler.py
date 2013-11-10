from kivy.clock import Clock


class PlayBackHandler():
    def __init__(self, bpm=0.0, updatesPerBeat=20.0):
        self._bpm = float(bpm)
        self._updatesPerBeat = float(updatesPerBeat)
        self._updateInterval = self._getIntervalTime(bpm=self._bpm,
                                                     updatesPerBeat=self._updatesPerBeat)
        self._currTime = 0.0
        self._lastTime = 0.0

        self._callbacks = []

    def setBpm(self, bpm):
        self._bpm = bpm
        self._updateInterval = self._getIntervalTime(bpm=self._bpm,
                                                     updatesPerBeat=self._updatesPerBeat)

    def addIntervalUpdateCallback(self, callback):
        self._callbacks.append(callback)

    def start(self):
        self._updateInterval = self._getIntervalTime(bpm=self._bpm,
                                                     updatesPerBeat=self._updatesPerBeat)
        self._scheduleNextUpdate()

    def stop(self):
        Clock.unschedule(self._onUpdate)
        self._updateInterval = 0.0

    def reset(self):
        self._currTime = 0.0

    def stopAndReset(self):
        self.stop()
        self.reset()

    def _getIntervalTime(self, bpm, updatesPerBeat):
        if bpm:
            return (1.0 / (float(bpm) / 60.0)) / float(updatesPerBeat)
        return 0.0

    def _scheduleNextUpdate(self):
        Clock.unschedule(self._onUpdate)
        if self._updateInterval:
            Clock.schedule_once(self._onUpdate, self._updateInterval)

    def _onUpdate(self, *args):
        self._currTime += 1.0 / self._updatesPerBeat
        for callback in self._callbacks:
            callback(self._currTime)

        self._scheduleNextUpdate()
