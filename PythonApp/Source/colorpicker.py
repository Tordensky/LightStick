import os
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.widget import Widget

Builder.load_file(os.getenv("FILE_PATH") + "/colorpicker.kv")


class CustomWheel(Widget):
    color = ListProperty((1, 1, 1, 1))
    screen_color = ListProperty((0.1, 0.5, 1, 1))
    bpm = NumericProperty(0.0)
    steps_per_beat = NumericProperty(24.0)
    fade_time_in_beats = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super(CustomWheel, self).__init__(**kwargs)
        self.new_color = (0, 0, 0, 0)

        self._fade_time_step_size = 1 / 0.25
        self._remaining_fade_time = 0.0

        self.IDX_RED = 0
        self.IDX_GREEN = 1
        self.IDX_BLUE = 2
        self.color_step_size = [0.0, 0.0, 0.0]

    def on_color(self, instance, new_color):
        self.set_new_color(new_color)

    def _trigger_update_color(self, idx, new_color_value):
        color_value = new_color_value / 255.0
        if color_value > 1.0:
            color_value = 1.0
        self.color[idx] = color_value

    def _calc_fade_time_in_time(self):
        try:
            return (float(self.fade_time_in_beats) / float(self.bpm)) * 60.0
        except ZeroDivisionError:
            return 0.0

    def _calc_time_each_fade_step(self):
        try:
            beats_per_sec = float(self.bpm) / 60.0
            steps_per_sec = beats_per_sec * float(self.steps_per_beat)
            return 1.0 / steps_per_sec
        except ZeroDivisionError:
            return 0.0

    def _calc_number_of_steps(self):
        try:
            return self.fade_time_in_time / self._fade_time_step_size
        except ZeroDivisionError:
            return 0.0

    def set_new_color(self, new_color):
        self.fade_time_in_time = self._calc_fade_time_in_time()
        self._fade_time_step_size = self._calc_time_each_fade_step()
        self.new_color = new_color

        self._remaining_fade_time = self.fade_time_in_time

        self._set_color_step_sizes()

        Clock.unschedule(self._color_fade_step)
        Clock.schedule_once(self._color_fade_step, self._fade_time_step_size)

    def _color_fade_step(self, *args):
        if self._is_in_color_fade():
            self._update_color_one_fade_step()
            Clock.schedule_once(self._color_fade_step, self._fade_time_step_size)
        else:
            self.screen_color = self.new_color

    def _is_in_color_fade(self):
        self._remaining_fade_time -= self._fade_time_step_size
        return self._remaining_fade_time > 0.0

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

if __name__ == "__main__":
    pass