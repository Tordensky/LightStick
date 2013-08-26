import kivy
import bpmcounter


kivy.require("1.7.2")

from kivy.app import App
from kivy.uix.gridlayout import GridLayout


class TestScreen(GridLayout):
    pass


class MyApp(App):
    def build(self):
        return TestScreen(cols=3)


if __name__ == "__main__":
    MyApp().run()
