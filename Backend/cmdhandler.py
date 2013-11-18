import json
import random
import threading
import time
import thread
import math
from randomshow import RandomShow
from config import serverconfig
from msvhandler import MsvController


class CommandHandler():
    def __init__(self):
        self._current_command = {}
        self._command_lock = threading.RLock()

        self._message_num_msv = MsvController(host=serverconfig.MSG_NUM_MSV_HOST,
                                              msv_id=serverconfig.MSG_NUM_MSV_ID)
        self._message_num_msv.set_msv_value(0)
        self._playback_msv = MsvController(host=serverconfig.PLAYBACK_MSV_HOST,
                                           msv_id=serverconfig.PLAYBACK_MSV_ID)
        self._current_message_num = self._message_num_msv.get_current_msv_value()

        self._init_and_start_random_mode()

    def _init_and_start_random_mode(self):
        self._is_in_random_mode = True
        self._random_show_helper = RandomShow()
        self._time_before_entering_random_mode = serverconfig.ENTER_RANDOM_MODE_AFTER_SEC

        thread.start_new_thread(self._random_cmd_handler, ())

    def _end_random_mode(self):
        self._is_in_random_mode = False

    def _reset_time_to_enter_random_mode(self):
        self._time_before_entering_random_mode = serverconfig.ENTER_RANDOM_MODE_AFTER_SEC

    def set_current_command(self, cmd_data, command_from_server=True):
        if command_from_server:
            self._is_in_random_mode = False
            self._reset_time_to_enter_random_mode()

        print "before", self._message_num_msv.get_current_msv_value()
        self._current_message_num += self._message_num_msv.get_current_msv_value() + 1

        with self._command_lock:
            self._current_command = cmd_data
            self._message_num_msv.set_msv_value(self._current_message_num)
            print "after", self._message_num_msv.get_current_msv_value()

    def get_current_command(self):
        self._message = {"cmdNum": self._current_message_num,
                         "data": self._current_command}

        return json.dumps(self._message)

    def _random_cmd_handler(self):
        while True:
            while self._is_in_random_mode:
                random_show = self._random_show_helper.get_random_show()

                timestamp = self._calculate_next_cmd_timestamp()
                random_show["MSV_TIME"] = timestamp

                self.set_current_command(random_show, command_from_server=False)

                time_to_next_random_show = random.randrange(serverconfig.RANDOM_INTERVAL_SEC_MIN,
                                                            serverconfig.RANDOM_INTERVAL_SEC_MAX)
                time.sleep(time_to_next_random_show)

            while not self._is_in_random_mode:
                time.sleep(5)
                self._time_before_entering_random_mode -= 5
                if self._time_before_entering_random_mode <= 0:
                    self._is_in_random_mode = True

    def _calculate_next_cmd_timestamp(self):
        current_time = int(math.floor(self._playback_msv.get_current_msv_value()))
        current_time += serverconfig.RANDOM_BPM_DELAY_NEXT_SHOW
        return current_time
