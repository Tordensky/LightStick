import os
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from framehandler import FrameHandler

import bpmcounter

Builder.load_file(os.getenv("FILE_PATH") + "/scenemixer.kv")


class SceneMixer(Widget):
    def __init__(self, **kwargs):
        super(SceneMixer, self).__init__(**kwargs)
        self.frameHandler = FrameHandler()


class __TestScreenMixer(App):
    def build(self):
        return SceneMixer()

if __name__ == "__main__":
    test = __TestScreenMixer()
    test.run()