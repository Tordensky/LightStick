# Written by Ingar Arntzen, Motion Corporation.

import unittest
import time
import socket
import scheduler
import errno
import pymsv.util.epollscheduler as scheduler
import threading

DATA = "test"

class SchedulerTest(unittest.TestCase):

    def setUp(self):
        self.S = scheduler.Scheduler()
        self.thread = threading.Thread(target=self.S.run)
        self.thread.start()

    def tearDown(self):
        self.S.stop()
        self.thread.join()

    def test_timeout(self):
        self.S.set_timeout(0.2, self.handle_timeout, anchor=time.time(), msg="msg")
        time.sleep(0.4)

    def handle_timeout(self, info, msg):
        error =  time.time() - info['ts']
        self.assertTrue(error >= 0)
        self.assertTrue(error <= 0.01)
        self.assertTrue(msg == "msg")
        print info, msg


    def test_periodic(self):
        now = time.time()
        self.S.set_interval(0.2, self.handle_timeout, anchor=now, limit=4, msg="msg")
        time.sleep(1.0)

    def test_cancel(self):
        self.S.set_interval(0.2, self.handle_timeout_cancel, limit=4)
        time.sleep(1.0)

    def handle_timeout_cancel(self, info, msg):
        print info, msg
        self.assertTrue(info['count'] < 2)
        if info['count'] == 1:
            self.S.cancel_timeout(info['tid'])


    def test_socket_io(self):

        self.test_done_event = threading.Event()

        # Create Listening Socket
        port = 8888
        host = None 
        sock_family = socket.AF_INET
        for res in socket.getaddrinfo(host, 
                                      port,
                                      sock_family,
                                      socket.SOCK_STREAM, 0,
                                      socket.AI_PASSIVE):
            
            af, socktype, proto, canonname, sa = res
            server_sock = socket.socket(af, socktype, proto)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(sa)
            server_sock.listen(5) 
            break

        # Register Selectable with Scheduler
        s = scheduler.SocketSelectable(server_sock)
        self.S.register_selectable(s)
        s.set_readable_handler(self._handle_server_accept)
        s.enter_read_set()

        # Connect and send request
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect(sa)
        client_sock.send(DATA)
        print "Send request client"

        # Register Selectable with Scheduler
        client_sock.setblocking(0)
        s = scheduler.SocketSelectable(client_sock)
        self.S.register_selectable(s)
        s.set_readable_handler(self._handle_client_read)
        s.set_error_handler(self._handle_client_error)
        s.enter_read_set()

        # Wait
        self.test_done_event.wait()
        self.S.stop()


    def _handle_server_accept(self, selectable):
        try:
            sock, addr = selectable.sock.accept()
            # Register Selectable with Scheduler
            sock.setblocking(0)
            s = scheduler.SocketSelectable(sock)
            self.S.register_selectable(s)
            s.set_readable_handler(self._handle_server_read)
            s.set_error_handler(self._handle_server_error)
            s.enter_read_set()
        except socket.error:
            return None

    def _handle_server_read(self, s):
        sock = s.sock
        # echo
        data = ""
        try:
            data = sock.recv(1024)
        except socket.error as e:
            if e[0] != errno.EAGAIN:
                s.handle_error(e[0])
            return
        if not data:
            s.handle_error(errno.EPIPE)
            return
        self.assertEqual(data, DATA)
        print "Got request, sent response", data
        sock.send(data)

    def _handle_client_read(self, s):
        sock = s.sock
        # echo
        data = ""
        try:
            data = sock.recv(1024)
        except socket.error as e:
            if e[0] != errno.EAGAIN:
                s.handle_error(e[0])
            return
        if not data:
            s.handle_error(errno.EPIPE)
            return
        self.assertEqual(data, DATA)
        print "Got response", data
        sock.close()
        print "Closed sock client"


    def handle_client_disconnect(self):
        print "Client disconnect handler"
        self.test_done_event.set()

    def _handle_client_error(self, s, e):
        print "Client error", e
        self.handle_client_disconnect()

    def _handle_server_error(self, s, e):
        print "Server error", e
        self.handle_client_disconnect()


##############################################
# MAIN
##############################################

if __name__ == '__main__':
    
    unittest.main()
    print "Done"
