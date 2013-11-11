import json
import os
import random
from config import serverconfig


class RandomShow():
    def __init__(self):
        self.PATH = serverconfig.RANDOM_SHOW_FOLDER

    def get_random_show(self):
        list_of_show_files = self._list_all_show_files()

        random_show = random.choice(list_of_show_files)
        with open(random_show, "r") as show_file:
            data = show_file.read()
            return json.loads(data)

    def _list_all_show_files(self):
        file_list = []
        for root, dirs, files in os.walk(self.PATH):
            for file in files:
                if file.endswith(".show"):
                    file_list.append(os.path.join(root, file))
        return file_list
