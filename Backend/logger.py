from collections import defaultdict
import json
import threading
import time
import thread
import config


class Logger():
    def __init__(self):
        self._logFileName = "%s%s%d%s" % (config.LOG_FILE_PATH,
                                          config.LOG_FILE_NAME,
                                          time.time(),
                                          config.LOG_FILE_ENDING)

        self._logInterval = config.LOG_INTERVAL_IN_SEC

        self._ids = defaultdict(int)
        self._lock = threading.RLock()

    def start_logger(self):
        thread.start_new_thread(self._logger, ())

    def log_id(self, clientID):
        with self._lock:
            self._ids[clientID] += 1

    def _get_all_IDs_and_reset(self):
        with self._lock:
            ids = self._ids
            self._ids = defaultdict(int)
            return ids

    def _logger(self):
        self._add_header_to_log_file()
        while True:
            clients = self._get_all_IDs_and_reset()
            logRecord = {"time": time.asctime(),
                         "num clients": len(clients),
                         "history": clients}
            self._append_to_file(json.dumps(logRecord))
            time.sleep(self._logInterval)

    def _add_header_to_log_file(self):
        headerLine = "Start: %s, Interval: %d" % (time.asctime(),self._logInterval)
        self._append_to_file(headerLine)

    def _append_to_file(self, line):
        with open(self._logFileName, "a") as stream:
            stream.write(line + "\n")
