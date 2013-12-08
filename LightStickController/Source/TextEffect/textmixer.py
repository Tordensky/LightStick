import os
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.widget import Widget

Builder.load_file(os.getenv("FILE_PATH") + "/textmixer.kv")


class TextMixer(Widget):
    text = StringProperty("")

    def __init__(self, **kwargs):
        super(TextMixer, self).__init__(**kwargs)

