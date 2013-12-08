from kivy.event import EventDispatcher
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.lang import Builder

import os

BEAT_LIVE_WINDOW = 1 / 10.0
Builder.load_file(os.getenv("FILE_PATH") + "/bpmcounter.kv")


class BeatCounterBall(Widget):
    BALL_ALPHA_ON = 0.8
    BALL_ALPHA_OFF = 0.1
    BALL_SECONDS_TO_FLASH = 0.1

    alpha = NumericProperty(BALL_ALPHA_OFF)

    def flash(self, *args):
        self._flash_on()

    def _flash_on(self):
        self.alpha = self.BALL_ALPHA_ON
        Clock.unschedule(self._flash_off)
        Clock.schedule_once(self._flash_off, self.BALL_SECONDS_TO_FLASH)

    def _flash_off(self, *args):
        self.alpha = self.BALL_ALPHA_OFF


class BeatCounterScreen(Widget):
    counter_ball = ObjectProperty(None)
    beat_value = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(BeatCounterScreen, self).__init__(**kwargs)

    def flash(self, *args):
        self.counter_ball.flash()

    def setScreenValue(self, screenValue):
        self.beat_value.text = str("%.1f" % screenValue)


class BeatCounter(Widget, EventDispatcher):
    MIN_SAMPLE_TIME = 0.01
    MAX_NUM_SAMPLES = 4

    beat_counter_screen = ObjectProperty(None)

    button_up = ObjectProperty(None)
    button_down = ObjectProperty(None)

    last_sample = 0.0
    avg_sample_time = 1.0

    beat_value = NumericProperty(0)

    trigger = BooleanProperty(False)

    samples = []

    def __init__(self, **kwargs):
        self.register_event_type('on_beat_trigger')
        super(BeatCounter, self).__init__(**kwargs)

        self.lastTime = 0.0
        Clock.schedule_once(self.set_new_bpm, 1 / 4.0)

    def on_beat_trigger(self, *args):
        pass

    def button_press(self):
        self._set_sample_time()
        self.set_new_bpm()

    def calculate_diff_value_for_bpm(self):
        return self.avg_sample_time / (600 / self.avg_sample_time)

    def bpm_button_press(self, callback):
        callback()
        Clock.schedule_interval(callback, 1 / 4.)

    def bpm_button_release(self, callback):
        Clock.unschedule(callback)

    def bpm_up(self, *args):
        self.avg_sample_time -= self.calculate_diff_value_for_bpm()
        self.set_new_bpm()

    def bpm_down(self, *args):
        self.avg_sample_time += self.calculate_diff_value_for_bpm()

        if self.avg_sample_time < 0.0:
            self.avg_sample_time = 0.0

        self.set_new_bpm()

    def sample_time_to_BPM(self, sample_time):
        return round(60 / float(sample_time), 1)

    def set_new_bpm(self, *args):
        self.beat_value = self.sample_time_to_BPM(self.avg_sample_time)

        self.beat_counter_screen.setScreenValue(self.beat_value)
        if self.avg_sample_time > 0.0:
            Clock.unschedule(self.on_beat)
            self.on_beat()

    def on_beat(self, *args):
        self.dispatch('on_beat_trigger')
        self.beat_counter_screen.flash()

        nextUpdateIn = (60 / self.beat_value)

        Clock.schedule_once(self.on_beat, nextUpdateIn)

    def _set_sample_time(self):
        if self.last_sample == 0.0:
            self.last_sample = Clock.get_time()
        else:
            new_sample = Clock.get_time()
            new_sample_time = new_sample - self.last_sample
            self._insert_new_sample(new_sample_time)
            self.last_sample = new_sample

            self.avg_sample_time = self._get_avg_from_samples()

        Clock.unschedule(self._reset_timer)
        Clock.schedule_once(self._reset_timer, 3)

    def _insert_new_sample(self, sample):
        if sample > self.MIN_SAMPLE_TIME:
            self.samples.append(sample)

            if len(self.samples) > self.MAX_NUM_SAMPLES:
                self.samples.pop(0)
        else:
            print 'error value'

    def _get_avg_from_samples(self):
        values = 0.0
        for sample in self.samples:
            values += sample

        values /= float(len(self.samples))
        return values

    def _reset_timer(self, ds):
        self.last_sample = 0.0
        self.samples = []
