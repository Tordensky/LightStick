from kivy.lang import Builder
from kivy.properties import ObjectProperty, ListProperty, BoundedNumericProperty
from kivy.uix.widget import Widget

#import os
#Builder.load_file(os.getcwd() + "/colorpicker.kv")

Builder.load_file("/workspace/LightStick/KiviTest/colorpicker.kv")


class CustomWheel(Widget):
    color = ListProperty((1, 1, 1, 1))
    color_red = BoundedNumericProperty(255)
    #hsv = ListProperty((1, 1, 1))

    #wheel = ObjectProperty(None)

    def on_color(self, instance, value):
        print instance, value

    def on_color_red(self, instance, value):
        print instance, value


if __name__ == "__main__":
    pass