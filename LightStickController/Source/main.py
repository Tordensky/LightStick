import json
import os, kivy, bpmcounter, colorpicker, msvcontroller
from kivy.lang import Builder
from kivy.properties import NumericProperty, ListProperty
import math
from HttpWebClient import HttpClient


Builder.load_file(os.getenv("FILE_PATH") + "/my.kv")

kivy.require("1.7.2")

from kivy.app import App
from kivy.uix.widget import Widget


class WebTest(Widget):
    color = ListProperty([0, 0, 0, 0])

    def __init__(self, **kwargs):
        super(WebTest, self).__init__(**kwargs)
        self.httpClient = HttpClient("localhost", 8080)

    def on_color(self, *args):
        print "COLOR WEB:", args
        print "HEX:", self.colorToHex(args[1])
        msg = {"command": {"color": self.colorToHex(args[1])}}
        self.httpClient.postJson(json.dumps(msg), "/command")

    def colorToHex(self, color):
        r = self._kivyColorToInt(color[0])
        g = self._kivyColorToInt(color[1])
        b = self._kivyColorToInt(color[2])
        hexColor = ("#%02x%02x%02x" % (r, g, b))
        return hexColor

    def _kivyColorToInt(self, value):
        return int(math.floor(255 * value))


class TestScreen(Widget):
    def __init__(self, **kwargs):
        super(TestScreen, self).__init__(**kwargs)
        print kwargs


class MyApp(App):
    header_size = NumericProperty(20)

    def build(self):
        return TestScreen()


if __name__ == "__main__":
    MyApp().run()
