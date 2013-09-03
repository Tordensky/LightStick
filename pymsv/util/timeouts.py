# Written by Ingar Arntzen, Motion Corporation

"""This implements a timeout thread supporting single timeouts and
periodic timeouts. The implementation supports a large number of
timeouts, but never employs more than a single thread."""

import threading
import sys
import time
import heapq
import Queue

##############################################
# PRIORITY QUEUE
##############################################

class PriorityQueue:

    """This implements a priority queue based on heapq module.
    The priority queue is kept sorted on keys, in ascending order.
    Key not required to be unique.
    """

    def __init__(self):
        self.__array = []

    def is_empty(self):
        """Return true if priority queue is empty"""
        return not self.__array

    def peek(self):
        """Return first (key,value) pair. Return None if empty."""
        if self.__array:
            return self.__array[0]

    def pop(self):
        """Pop first (key, value) pair and return it. Return None if empty"""
        if self.__array:
            return heapq.heappop(self.__array) 

    def push(self, key, value):
        """Insert key,value pair into queue"""
        heapq.heappush(self.__array, (key, value))

    def clear(self):
        """Clear the priority queue"""
        self.__array = []


##############################################
# TIMEOUT MANAGER
##############################################

CMD_REGISTER = 1
CMD_CANCEL = 2

class TimeoutManager:

    """
    This implements a manager for timeouts.  A single thread will
    detect and callback on every timeout.  If no timeouts exists, no
    thread exists.

    A priority queue is used for keeping the timeout sorted. An instance
    """

    def __init__(self, stop_event=None):
       
        # Private data - only touched by client thread(s)
        self.__client_lock = threading.Lock() # protects clients from eachother
        self.__tid_counter = 0L 

        # Private data - only touched by run-thread
        self.__map = {} # tid -> data
        self.__pq = PriorityQueue()

        # Shared data (thread-safe)
        self.__stop_event = stop_event if stop_event != None else threading.Event()
        self.__request_queue = Queue.Queue()        

        # Run-thread
        self.__thread = threading.Thread(target=self.__run)

        
    def start(self):
        self.__thread.start()


    def set_timeout(self, delta, handler, anchor=None, msg=None):
        """Create a timeout
        Callbacks by timeout thread, even if delta==0."""
        return self.set_interval(delta, handler, limit=1, anchor=anchor, msg=msg)

    def set_interval(self, delta, handler,  limit=1, anchor=None, msg=None):
        """Create periodic timeout. 
        Callbacks by timeout thread, even if delta==0."""
        now = time.time()

        if limit == None: 
            limit = sys.maxint
        elif limit <= 0: 
            limit = 1
        if anchor == None: 
            anchor = now
        # anchor + delta < now TODO - support negative anchor in general
        if anchor + delta < now:
            anchor = now - delta
        if delta == None or delta < 0: 
            delta = 0.0
        
        _next = anchor + delta

        # Unique tid - timeout id
        tid = 0
        with self.__client_lock:
            tid = self.__tid_counter
            self.__tid_counter += 1

        record = {
             'handler': handler,
             'tid': tid,
             'anchor': anchor,
             'delta': delta,
             'count': 0,
             'limit': limit,
             'msg': msg,
             'next': _next,
             }

        self.__request_queue.put_nowait((CMD_REGISTER, record))
        return tid

    def cancel_timeout(self, tid):
        """Cancel timeout associated with tid."""
        self.__request_queue.put_nowait((CMD_CANCEL, tid))
        
    def __handle_cancel(self, tid):
        """Run-thread dequeued a cancel request"""
        if self.__map.has_key(tid):
            del self.__map[tid]

    def __handle_register(self, record):
        """Run-thread dequeued a register request"""
        tid = record['tid']
        _next = record['next']
        self.__map[tid] = record
        self.__pq.push(_next, tid)

    def __poll(self):
        """
        Poll priority queue to pop all due timeouts.
        Also does resheduling of periodic timeouts
        """
        _list = []
        _ts = time.time()
        while True:
            res = self.__pq.peek()
            if res == None or _ts <= res[0]: 
                break
            # Pop one entry
            timestamp, tid = self.__pq.pop()
            if self.__map.has_key(tid):
                to_record = self.__map[tid]
                # Increment counter
                to_record['count'] += 1
                # Re-schedule periodic timeouts
                if to_record['delta'] > 0.0 and to_record['count'] < to_record['limit']:
                    to_record['next'] = to_record['anchor'] + (to_record['count'] + 1) * to_record['delta']
                    self.__handle_register(to_record)
                    last = False
                # Clean up
                else:
                    last = True
                    del self.__map[tid]
                # Handle timeout
                _list.append((to_record, timestamp, last))
        return _list

    def __process(self, _list):
        """Process timeouts - list is result from poll"""
        for to_record, timestamp, last in _list:
            handler = to_record['handler']
            info = {
                'tid': to_record['tid'], 
                'ts': timestamp, 
                'delta': to_record['delta'],
                'anchor': to_record['anchor'],
                'count': to_record['count'], 
                'last': last, 
                }
            handler(info, to_record['msg'])

    def __wait(self):
        """Wait on new timeout, on incoming requests, but
        not longer than 1 sec - for join responsiveness"""
        delta = 1.0
        res = self.__pq.peek()
        if res != None:
            delta = res[0] - time.time()
            if delta < 0: return
        msg = None
        try:
            # Blocking wait on request queue
            msg = self.__request_queue.get(True, min(delta, 1.0))
            # Wait interrupted be incoming msg            
        except Queue.Empty:
            # Timeout - either because a timeout is due, or because
            # one second has passed. In either case - just continue
            # the run loop. If a timeout is due this will be picked up by
            # the poll method. If not - a new wait will be the result.
            return
        # Empty the request queue
        while msg != None:
            cmd, data = msg
            if cmd == CMD_REGISTER:
                self.__handle_register(data)
            elif cmd == CMD_CANCEL:
                self.__handle_cancel(data)
            try:
                msg = self.__request_queue.get(False)
            except Queue.Empty:
                msg = None

    def __run(self):
        """Timeout run-thread: poll for expired timeouts, process them and
        read incoming requests."""

        while not self.__stop_event.is_set():
            # Poll timeouts
            _list = self.__poll()
            # Process timeouts
            if _list:
                self.__process(_list)
            # Wait
            self.__wait()

        # Cleanup
        self.__pq.clear()
        self.__map = {}
        
                    
    def stop(self):
        """Request the timeout manager to stop. Cancel all timeouts."""
        self.__stop_event.set()

    def join(self, timeout=None):
        """Join timeout thread"""
        if self.__thread:
            self.__thread.join(timeout=timeout)

