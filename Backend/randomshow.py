import json
import os
import random
from config import serverconfig


class RandomShow():
    def __init__(self):
        self.PATH = serverconfig.RANDOM_SHOW_FOLDER

    def get_random_show(self):
        light_show_files = self._list_all_show_files()

        if len(light_show_files) == 0:
            return {}
        else:
            random_show = random.choice(light_show_files)
            with open(random_show, "r") as show_file:
                data = show_file.read()
                return json.loads(data)

    def _list_all_show_files(self):
        file_list = []
        for root, dirs, files in os.walk(self.PATH):
            for lightShowFile in files:
                if lightShowFile.endswith(".show"):
                    file_list.append(os.path.join(root, lightShowFile))
        return file_list
