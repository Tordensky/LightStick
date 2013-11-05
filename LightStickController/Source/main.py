import os
import kivy

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.config import Config

Builder.load_file(os.getenv("FILE_PATH") + "/main.kv")

kivy.require("1.7.2")

Config.set('graphics', 'width', '940')
Config.set('graphics', 'height', '700')


class WidgetScreen(Widget):
    def __init__(self, **kwargs):
        super(WidgetScreen, self).__init__(**kwargs)
        print kwargs


class LightStickApp(App):
    # Global path for storing last location of
    # opened and saved show files
    path = ""

    def build(self):
        return WidgetScreen()


if __name__ == "__main__":
    LightStickApp().run()
