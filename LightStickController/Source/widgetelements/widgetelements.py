import os
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout

Builder.load_file(os.getenv("FILE_PATH") + "/widgetElements.kv")


# A slider with customized steps
class CustomStepSlider(BoxLayout):
    label_value = StringProperty("")
    slider_value = NumericProperty(0)
    value = NumericProperty(0)
    step_values = ListProperty([])
    step_labels = ListProperty([])

    def on_slider_value(self, *args):
        idx = int(args[1])
        self.value = self.step_values[idx]
        self.label_value = self.step_labels[idx]