# Written by Ingar Arntzen, Motion Corporation.

import unittest
import timeouts
import time

class A: pass

class TimeoutTest(unittest.TestCase):

    def setUp(self):
        self.tm = timeouts.TimeoutManager()
        self.tm.start()
    def tearDown(self):
        self.tm.stop()

    def test_timeout(self):
        a = A()
        a.notified = False
        def timeout_handler(info, msg):
            a.notified = True
            error =  time.time() - info['ts']
            self.assertTrue(error >= 0)
            self.assertTrue(error <= 0.002)
            self.assertTrue(msg == "msg")
            print info, msg
            if info['last']:
                self.assertTrue(self.tm._TimeoutManager__pq.is_empty())

        self.tm.set_timeout(0.2, timeout_handler, anchor=time.time(), msg="msg")
        time.sleep(0.4)
        self.assertTrue(a.notified)

    def test_periodic(self):
        a = A()
        a.notified = False
        def timeout_handler(info, msg):
            a.notified = True
            error =  time.time() - info['ts']
            self.assertTrue(error >= 0)
            self.assertTrue(error <= 0.002)
            self.assertTrue(msg == "msg")
            print info, msg
            if info['last']:
                self.assertTrue(self.tm._TimeoutManager__pq.is_empty())

        now = time.time()
        self.tm.set_interval(0.2, timeout_handler, anchor=now, limit=4, msg="msg")
        time.sleep(1.0)
        self.assertTrue(a.notified)

    def test_cancel(self):
        a = A()
        a.notified = False
        self.tm.set_interval(0.2, self.handle_timeout_cancel, limit=4, msg=a)
        time.sleep(1.0)
        self.assertTrue(a.notified)

    def handle_timeout_cancel(self, info, msg):
        a = msg
        a.notified = True
        self.assertTrue(info['count'] < 2)
        if info['count'] == 1:
            self.tm.cancel_timeout(info['tid'])

    def test_immediate_cancel(self):
        a = A()
        a.notified = False
        def timeout_handler(info, msg):
            a.notified = True        
        tid = self.tm.set_timeout(0.3, timeout_handler)
        self.tm.cancel_timeout(tid)
        time.sleep(0.5)
        self.assertFalse(a.notified)







##############################################
# MAIN
##############################################

if __name__ == '__main__':
    
    unittest.main()
    print "Done"
