import kivy
kivy.require("1.7.2")

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock


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


class BeatCounterScreen(BoxLayout):
    counter_ball = ObjectProperty(None)
    beat_value = ObjectProperty(None)

    def update(self, sample_time):
        self.beat_value.text = str("%.1f" % (60 / sample_time))

        Clock.unschedule(self.counter_ball.flash)
        Clock.schedule_interval(self.counter_ball.flash, sample_time)


class BeatCounter(BoxLayout):
    TO_FAST_SAMPLE = 0.01
    MAX_NUM_SAMPLES = 8

    beat_counter_screen = ObjectProperty(None)

    last_sample = 0.0
    avg_sample_interval = 1.0

    samples = []

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
        if sample > self.TO_FAST_SAMPLE:
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


class TestScreen(GridLayout):
    pass


class MyApp(App):
    def build(self):
        return TestScreen(cols = 2)


if __name__ == "__main__":
    MyApp().run()
