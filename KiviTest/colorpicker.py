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
        self.target_color = (0, 0, 0, 0)

        self._fade_time = 5.0
        self._fade_step_size = 0.01
        self._cur_time = 0.0

    def on_color(self, instance, value):
        self.set_new_color(value)

    def _trigger_update_clr(self, idx, value):
        color_value = value / 255.0
        if color_value > 1.0:
            color_value = 1.0
        self.color[idx] = color_value

    def set_new_color(self, value):
        self.old_color = self.target_color
        self.target_color = value
        self._cur_time = self._fade_time
        Clock.unschedule(self._color_change_step)
        Clock.schedule_once(self._color_change_step, self._fade_step_size)

    def _color_change_step(self, *args):
        self._cur_time -= self._fade_step_size

        if not self._cur_time <= 0.0:
            current_fade_percent = (self._fade_time - self._cur_time) / self._fade_time
            self._set_new_screen_color(current_fade_percent)
            Clock.schedule_once(self._color_change_step, self._fade_step_size)
        else:
            self.screen_color = self.target_color

    def _set_new_screen_color(self, current_fade_percent):
        self._set_current_fade_color(0, current_fade_percent)
        self._set_current_fade_color(1, current_fade_percent)
        self._set_current_fade_color(2, current_fade_percent)

    def _set_current_fade_color(self, idx, current_time_percent):
        color_diff = (self.target_color[idx] - self.screen_color[idx])
        color_diff *= current_time_percent
        self.screen_color[idx] = self.screen_color[idx] + color_diff


if __name__ == "__main__":
    pass