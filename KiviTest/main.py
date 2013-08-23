import kivy

kivy.require("1.7.2")

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
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
    beat_counter_screen = ObjectProperty(None)

    first_sample = 0.0
    sample_interval = 1.0

    def button_press(self):
        self._set_sample()
        self.beat_counter_screen.update(self.sample_interval)

    def _set_sample(self):
        if self.first_sample == 0.0:
            self.first_sample = Clock.get_time()
        else:
            second_sample = Clock.get_time()
            self.sample_interval = second_sample - self.first_sample
            self.first_sample = second_sample

        Clock.unschedule(self._reset_timer)
        Clock.schedule_interval(self._reset_timer, 3)

    def _reset_timer(self, ds):
        self.first_sample = 0.0


class MyApp(App):
    def build(self):
        return BeatCounter()


if __name__ == "__main__":
    MyApp().run()