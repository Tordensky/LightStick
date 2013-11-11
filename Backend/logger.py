from collections import defaultdict
import json
import threading
import time
import thread
import config


class Logger():
    def __init__(self):
        self._log_file_name = "%s%s%d%s" % (config.LOG_FILE_PATH,
                                            config.LOG_FILE_NAME,
                                            time.time(),
                                            config.LOG_FILE_ENDING)

        self._log_interval = config.LOG_INTERVAL_IN_SEC

        self._ids = defaultdict(int)
        self._lock = threading.RLock()

    def start_logger(self):
        thread.start_new_thread(self._logger, ())

    def add_log_id(self, clientID):
        with self._lock:
            self._ids[clientID] += 1

    def _get_all_IDs_and_reset(self):
        with self._lock:
            ids = self._ids
            self._ids = defaultdict(int)
            return ids

    def _logger(self):
        self._write_header_to_log_file()
        while True:
            clients = self._get_all_IDs_and_reset()
            logRecord = {"time": time.asctime(),
                         "num clients": len(clients),
                         "history": clients}
            self._append_to_file(json.dumps(logRecord))
            time.sleep(self._log_interval)

    def _write_header_to_log_file(self):
        header_line = "Start: %s, Interval: %d" % (time.asctime(),
                                                   self._log_interval)
        self._append_to_file(header_line)

    def _append_to_file(self, line):
        with open(self._log_file_name, "a") as log_file:
            log_file.write(line + "\n")
