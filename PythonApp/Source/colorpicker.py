import os
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.widget import Widget

Builder.load_file(os.getenv("FILE_PATH") + "/colorpicker.kv")


class CustomWheel(Widget):
    color = ListProperty((1, 1, 1, 1))
    screen_color = ListProperty((0.1, 0.5, 1, 1))
    bpm = NumericProperty(60)
    steps_per_beat = NumericProperty(16)
    fade_time = NumericProperty(6)

    def __init__(self, **kwargs):
        super(CustomWheel, self).__init__(**kwargs)
        self.new_color = (0, 0, 0, 0)

        self._fade_time_step_size = 1 / 0.25
        self._current_fade_time = 0.0

        self.IDX_RED = 0
        self.IDX_GREEN = 1
        self.IDX_BLUE = 2
        self.color_step_size = [0.0, 0.0, 0.0]

    def _calc_fade_time(self):
        return (float(self.fade_time) / float(self.bpm)) * 60.0

    def _calc_time_fade_step(self):
        return 1.0 / float(self.steps_per_beat)

    def _calc_number_of_steps(self):
        return self.fade_time / self._fade_time_step_size

    def on_color(self, instance, new_color):
        self.set_new_color(new_color)

    def _trigger_update_color(self, idx, new_color_value):
        color_value = new_color_value / 255.0
        if color_value > 1.0:
            color_value = 1.0
        self.color[idx] = color_value

    def set_new_color(self, new_color):
        self.fade_time = self._calc_fade_time()
        self._fade_time_step_size = self._calc_time_fade_step()
        self.new_color = new_color

        self._current_fade_time = self.fade_time

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
        self._current_fade_time -= self._fade_time_step_size
        return self._current_fade_time > 0.0

    def _get_color_step_size(self, idx):
        color_diff = (self.new_color[idx] - self.screen_color[idx])
        return float(color_diff) / float(self._calc_number_of_steps())

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

    def _calculate_fade_step_time_to_percent(self):
        return (self.fade_time - self._current_fade_time) / self.fade_time


if __name__ == "__main__":
    pass