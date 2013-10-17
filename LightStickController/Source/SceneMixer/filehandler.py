import os
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup

Builder.load_file(os.getenv("FILE_PATH") + "/filehandler.kv")


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty("")


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty("")


class FileHandler():
    #loadFile = ObjectProperty(None)
    #savefile = ObjectProperty(None)

    def __init__(self):
        self.fileData = ""

        self.loadReadyCallback = None
        self.path = ""

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self, loadCallback=None):
        self.loadReadyCallback = loadCallback
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup, path=self.path)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self, saveString):
        self.fileData = saveString
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup, path=self.path)
        self._popup = Popup(title="Save file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        self.path = path
        with open(os.path.join(path, filename[0])) as stream:
            self.fileData = stream.read()

        self.dismiss_popup()

        if self.loadReadyCallback is not None:
            self.loadReadyCallback(self.fileData)

    def save(self, path, filename):
        self.path = path
        filename += ".show"
        with open(os.path.join(path, filename), 'w') as stream:
            stream.write(self.fileData)

        self.dismiss_popup()
