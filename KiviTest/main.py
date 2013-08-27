import kivy
from bpmcounter import *
import colorpicker

kivy.require("1.7.2")

from kivy.app import App
from kivy.uix.widget import Widget


class TestScreen(Widget):
    def __init__(self, **kwargs):
        super(TestScreen, self).__init__(**kwargs)
        print kwargs


class MyApp(App):
    def build(self):
        return colorpicker.CustomWheel()


if __name__ == "__main__":
    MyApp().run()
