import os
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.widget import Widget
from SceneMixer import PlayBackHandler

Builder.load_file(os.getenv("FILE_PATH") + "/colorpicker.kv")


class CustomWheel(Widget):
    IDX_RED = 0
    IDX_GREEN = 1
    IDX_BLUE = 2

    color = ListProperty((1, 1, 1, 1))
    screen_color = ListProperty((0.1, 0.5, 1, 1))

    bpm = NumericProperty(60.0)

    fade_time_in_beats = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super(CustomWheel, self).__init__(**kwargs)
        self.newColor = (0, 0, 0, 0)

        self.__color_step_size = [0.0, 0.0, 0.0]

        self.__updatesPerBeat = 32

        self.__playBackHandler = PlayBackHandler(bpm=60.0, updatesPerBeat=self.__updatesPerBeat)
        self.__playBackHandler.addIntervalUpdateCallback(self.fadeStepCallback)

    def on_bpm(self, obj, newBpm):
        self.__playBackHandler.setBpm(newBpm)

    def on_color(self, obj, newColor):
        self.set_new_color(newColor)

    def set_new_color(self, newColor):
        self.newColor = newColor
        if self.fade_time_in_beats > 0.0:
            self.__set_color_step_sizes()
            self.__playBackHandler.start()
        else:
            self.screen_color = newColor

    def fadeStepCallback(self, time):
        if self.fade_time_in_beats <= time:
            self.__playBackHandler.stopAndReset()
        else:
            self.__update_color_one_fade_step()

    def setValueFromSlider(self, idx, new_color_value):
        color_value = new_color_value / 255.0
        if color_value > 1.0:
            color_value = 1.0
        self.color[idx] = color_value

    def __calc_number_of_steps(self):
            return float(self.fade_time_in_beats) * self.__updatesPerBeat

    def __get_color_step_size(self, idx):
        try:
            color_diff = (self.newColor[idx] - self.screen_color[idx])
            return float(color_diff) / float(self.__calc_number_of_steps())
        except ZeroDivisionError:
            return 0.0

    def __set_color_step_sizes(self):
        self.__color_step_size[self.IDX_RED] = self.__get_color_step_size(self.IDX_RED)
        self.__color_step_size[self.IDX_GREEN] = self.__get_color_step_size(self.IDX_GREEN)
        self.__color_step_size[self.IDX_BLUE] = self.__get_color_step_size(self.IDX_BLUE)

    def __update_color_one_fade_step(self):
        self.__update_color_step_helper(self.IDX_RED)
        self.__update_color_step_helper(self.IDX_GREEN)
        self.__update_color_step_helper(self.IDX_BLUE)

    def __update_color_step_helper(self, idx):
        self.screen_color[idx] += self.__color_step_size[idx]
