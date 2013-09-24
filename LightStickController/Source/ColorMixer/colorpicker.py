import os
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, BooleanProperty
from kivy.uix.widget import Widget

Builder.load_file(os.getenv("FILE_PATH") + "/colorpicker.kv")


class CustomWheel(Widget):
    IDX_RED = 0
    IDX_GREEN = 1
    IDX_BLUE = 2

    color = ListProperty((1, 1, 1, 1))
    screen_color = ListProperty((0.1, 0.5, 1, 1))

    bpm = NumericProperty(0.0)
    trigger = BooleanProperty(False)

    fade_time_in_beats = NumericProperty(1.0)
    steps_per_beat = NumericProperty(1)

    def __init__(self, **kwargs):
        super(CustomWheel, self).__init__(**kwargs)
        self.new_color = (0, 0, 0, 0)

        self._fade_step_in_time = 0.0
        self._remaining_fade_time = 0.0

        self.execute_change_color = False
        self.color_step_size = [0.0, 0.0, 0.0]

    def on_color(self, instance, new_color):
        self.new_color = new_color
        if self.trigger:
            self.set_new_color()
        else:
            self.execute_change_color = True

    # TRIGGER SIGNAL FROM BPM COUNTER OR OTHER CONTROLLING UNIT
    def on_trigger(self, *args):
        if args[1]:
            if self.execute_change_color:
                self.execute_change_color = False
                self.set_new_color()

    def _trigger_update_color(self, idx, new_color_value):
        color_value = new_color_value / 255.0
        if color_value > 1.0:
            color_value = 1.0
        self.color[idx] = color_value

    def _calc_fade_time_in_time(self):
        try:
            return (float(self.fade_time_in_beats) / float(self.bpm)) * 60.0
        except ZeroDivisionError:
            print "ZERO DIV ERROR fade time"
            return 0.0

    # TODO does not return the correct result!
    def _calc_fade_step_in_time(self):
        try:
            beats_per_sec = float(self.bpm) / 60.0
            steps_size_in_time = float(beats_per_sec) / float(self.steps_per_beat)

            fade_time = self._calc_fade_time_in_time()
            if steps_size_in_time > fade_time:
                return fade_time
            return steps_size_in_time
        except ZeroDivisionError:
            print "ZERO DIV ERROR fade step"
            return 0.0

    def _calc_number_of_steps(self):
        try:
            return self.fade_time_in_time / self._fade_step_in_time
        except ZeroDivisionError:
            print "ZERO DIV ERROR num step"
            return 0.0

    def set_new_color(self):
        self.fade_time_in_time = self._calc_fade_time_in_time()
        self._fade_step_in_time = self._calc_fade_step_in_time()

        self._remaining_fade_time = self.fade_time_in_time

        self._set_color_step_sizes()

        # TODO fix if fade step time is larger than fade time
        Clock.unschedule(self._execute_fade_step)
        Clock.schedule_once(self._execute_fade_step, self._fade_step_in_time)

    def _execute_fade_step(self, *args):
        if self._is_in_color_fade():
            self._update_color_one_fade_step()
            Clock.schedule_once(self._execute_fade_step, self._fade_step_in_time)
        else:
            self.screen_color = self.new_color

    def _is_in_color_fade(self):
        if self._remaining_fade_time <= 0.0:
            return False
        self._remaining_fade_time -= self._fade_step_in_time
        return self._remaining_fade_time >= 0.0

    def _get_color_step_size(self, idx):
        try:
            color_diff = (self.new_color[idx] - self.screen_color[idx])
            return float(color_diff) / float(self._calc_number_of_steps())
        except ZeroDivisionError:
            return 0.0

    def _set_color_step_sizes(self):
        self.color_step_size[self.IDX_RED] = self._get_color_step_size(self.IDX_RED)
        self.color_step_size[self.IDX_GREEN] = self._get_color_step_size(self.IDX_GREEN)
        self.color_step_size[self.IDX_BLUE] = self._get_color_step_size(self.IDX_BLUE)

    def _update_color_one_fade_step(self):
        self._update_color_step_helper(self.IDX_RED)
        self._update_color_step_helper(self.IDX_GREEN)
        self._update_color_step_helper(self.IDX_BLUE)

    def _update_color_step_helper(self, idx):
        self.screen_color[idx] += self.color_step_size[idx]
