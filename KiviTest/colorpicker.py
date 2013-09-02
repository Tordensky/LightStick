from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, ListProperty, BoundedNumericProperty
from kivy.uix.widget import Widget

import os
#Builder.load_file(os.getcwd() + "/colorpicker.kv")

Builder.load_file("/workspace/LightStick/KiviTest/colorpicker.kv")


class CustomWheel(Widget):
    color = ListProperty((1, 1, 1, 1))
    screen_color = ListProperty((0.1, 0.5, 1, 1))

    def __init__(self, **kwargs):
        super(CustomWheel, self).__init__(**kwargs)
        self.new_color = (0, 0, 0, 0)

        self._fade_time = 5.0
        self._fade_time_step_size = 0.01
        self._current_fade_time = 0.0

        self.IDX_RED = 0
        self.IDX_GREEN = 1
        self.IDX_BLUE = 2

    def on_color(self, instance, new_color):
        self.set_new_color(new_color)

    def set_new_color(self, new_color):
        self.new_color = new_color
        self._current_fade_time = self._fade_time

        Clock.unschedule(self._color_fade_step)
        Clock.schedule_once(self._color_fade_step, self._fade_time_step_size)

    def _trigger_update_color(self, idx, new_color_value):
        color_value = new_color_value / 255.0
        if color_value > 1.0:
            color_value = 1.0
        self.color[idx] = color_value

    def _color_fade_step(self, *args):
        self._current_fade_time -= self._fade_time_step_size

        if self._is_in_color_fade():
            fade_time_step_in_percent = self._calculate_fade_step_time_to_percent()
            self._update_current_fade_color(fade_time_step_in_percent)
            Clock.schedule_once(self._color_fade_step, self._fade_time_step_size)
        else:
            self.screen_color = self.new_color

    def _is_in_color_fade(self):
        return self._current_fade_time > 0.0

    def _calculate_fade_step_time_to_percent(self):
        return (self._fade_time - self._current_fade_time) / self._fade_time

    def _update_current_fade_color(self, fade_time_step_in_percent):
        self._set_current_fade_color(self.IDX_RED, fade_time_step_in_percent)
        self._set_current_fade_color(self.IDX_GREEN, fade_time_step_in_percent)
        self._set_current_fade_color(self.IDX_BLUE, fade_time_step_in_percent)

    def _set_current_fade_color(self, idx, fade_time_step_in_percent):
        color_diff = (self.new_color[idx] - self.screen_color[idx])
        color_diff *= fade_time_step_in_percent
        self.screen_color[idx] = self.screen_color[idx] + color_diff


if __name__ == "__main__":
    pass