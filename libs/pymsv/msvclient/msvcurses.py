# Written by Ingar Arntzen, Norut & Motion Corporation

import curses
import locale
import threading
import time

from msvclient.client import Client, Msv


#################################################
# MSVSCREEN
#################################################

class MsvScreen:

    """Visualise a single MSV in the terminal"""

    def __init__(self, host, msvid):
        self._stop_event = threading.Event()
        self._client = Client(host)
        self._client.start()
        self._msv = Msv(self._client, msvid)
        self._msv.add_handler(self.update_handler)

    def update_handler(self, msv_data):
        #print "Update", msv_data
        pass

    def stop(self):
        self._client.stop()
        self._stop_event.set()

    def join(self):
        self._client.join()

    def run(self, scr):
        scr.nodelay(True)        
        locale.setlocale(locale.LC_ALL, '')
        code = locale.getpreferredencoding()
        scr.addstr("MSV")
        scr.addstr(2, 0, "P")
        scr.addstr(3, 0, "V")
        scr.addstr(4, 0, "A")
        while not self._stop_event.is_set():
            vector = self._msv.query()
            scr.addstr(2, 5, "%5.2f" % vector[0])
            scr.addstr(3, 5, "%5.2f" % vector[1])
            scr.addstr(4, 5, "%5.2f" % vector[2])
            c = scr.getch()
            if c == -1:
                time.sleep(0.1)
                continue
            if c == 113:
                self._stop_event.set()
    
#################################################
# MAIN
#################################################

if __name__ == '__main__':
    
    HOST = "mcorp.no"
    MSVID = 5

    s = MsvScreen(HOST, MSVID)
    try:
        curses.wrapper(s.run)
    finally:
        curses.endwin()
        s.stop()
        s.join()


