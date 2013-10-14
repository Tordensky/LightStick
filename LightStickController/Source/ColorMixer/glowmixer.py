import os
from kivy.lang import Builder
from kivy.uix.widget import Widget

Builder.load_file(os.getenv("FILE_PATH") + "/glowmixer.kv")


class GlowMixer(Widget):
    pass


if __name__ == "__main__":
    pass