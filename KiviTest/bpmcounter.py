from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.lang import Builder

Builder.load_file("/workspace/LightStick/KiviTest/bpmcounter.kv")


class WidgetHeader(Widget):

    def __init__(self, **kwargs):
        super(WidgetHeader, self).__init__(**kwargs)


class BeatCounterBall(Widget):
    alpha = NumericProperty(0.1)

    def flash(self, dt):
        self._flash_on()

    def _flash_on(self):
        self.alpha = 0.8
        Clock.unschedule(self._flash_off)
        Clock.schedule_once(self._flash_off, 0.1)

    def _flash_off(self, dt):
        self.alpha = 0.1


class UpDownMenu(Widget):
    up = ObjectProperty(None)
    down = ObjectProperty(None)

    def bpm_up(self):
        print "up"

    def bpm_down(self):
        print "down"


class BeatCounterScreen(Widget):
    counter_ball = ObjectProperty(None)
    beat_value = ObjectProperty(None)

    def update(self, sample_time):
        self.beat_value.text = str("%.1f" % (60 / sample_time))

        Clock.unschedule(self.counter_ball.flash)
        Clock.schedule_interval(self.counter_ball.flash, sample_time)


class BeatCounter(Widget):
    MIN_SAMPLE_TIME = 0.01
    MAX_NUM_SAMPLES = 4

    beat_counter_screen = ObjectProperty(None)
    up_down_menu = ObjectProperty(None)

    last_sample = 0.0
    avg_sample_interval = 1.0

    samples = []

    def __init__(self, **kwargs):
        super(BeatCounter, self).__init__(**kwargs)

    def test(self):
        print "hurra"

    def button_press(self):
        self._set_sample_time()
        self.beat_counter_screen.update(self.avg_sample_interval)

    def _set_sample_time(self):
        if self.last_sample == 0.0:
            self.last_sample = Clock.get_time()
        else:
            new_sample = Clock.get_time()
            new_sample_time = new_sample - self.last_sample
            self._insert_new_sample(new_sample_time)
            self.last_sample = new_sample

            self.avg_sample_interval = self._get_avg_from_samples()

        Clock.unschedule(self._reset_timer)
        Clock.schedule_interval(self._reset_timer, 3)

    def _reset_timer(self, ds):
        self.last_sample = 0.0
        self.samples = []

    def _insert_new_sample(self, sample):
        if sample > self.MIN_SAMPLE_TIME:
            self.samples.append(sample)

            if len(self.samples) > self.MAX_NUM_SAMPLES:
                self.samples.pop(0)
            print self.samples
        else:
            print 'error value'

    def _get_avg_from_samples(self):
        values = 0.0
        for sample in self.samples:
            values += sample

        values /= float(len(self.samples))
        return values


if __name__ == "__main__":
    pass