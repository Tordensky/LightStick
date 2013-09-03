import os, kivy, bpmcounter, colorpicker
from kivy.lang import Builder
from kivy.properties import NumericProperty

Builder.load_file(os.getenv("FILE_PATH") + "/my.kv")

kivy.require("1.7.2")

from kivy.app import App
from kivy.uix.widget import Widget


class TestScreen(Widget):
    def __init__(self, **kwargs):
        super(TestScreen, self).__init__(**kwargs)
        print kwargs


class MyApp(App):
    header_size = NumericProperty(26)

    def build(self):
        return TestScreen()


if __name__ == "__main__":
    MyApp().run()
