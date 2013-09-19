# Written by Ingar Arntzen, Motion Corporation

"""This implements a scheduler for non-blocking, select based execution."""

import socket
import select
import errno
import threading
import multiprocessing
import traceback
import time
import timeouts

from pymsv.util.mylog import *

##############################################
# SCHEDULER
##############################################

class Scheduler:

    def __init__(self, name, stop_event=None):
        
        # Execution
        self._name = name
        self._stop_event = stop_event if stop_event != None else multiprocessing.Event()

        # IO
        self._read_set = [] # selectables
        self._write_set = [] # selectables
        self._readable_handlers = {} # selectable -> handle_readable
        self._writeable_handlers = {} # selectable -> handle_writeable
        self._error_handlers = {} # selectable -> handle_error
        self._selectables = []

        # Timeouts
        self._tm = timeouts.TimeoutManager(stop_event=self._stop_event)
        self._timeout_pending = {} # tid -> handler

        # Timeout Queue
        self._timeout_queue = multiprocessing.Queue()
        s = ReadQueueSelectable(self._timeout_queue)
        self.register_selectable(s)
        s.set_readable_handler(self._handle_timeout_queue_readable)
        s.enter_read_set()

        self.log = MyLog().log

    def get_name(self):
        return self._name
        
    ##############################################
    # SELECTABLES
    ##############################################

    def register_selectable(self, selectable, addr=None):
        """
        Add a selectable to the scheduler
        """
        selectable._S = self
        self._selectables.append(selectable)

    def count_selectables(self):
        """Return number of registrered selectables"""
        return len(self._selectables)

    def unregister_selectable(self, selectable):
        """
        Remove a selectable from the scheduler
        """
        selectable.cleanup()
        if selectable in self._selectables:
            self._selectables.remove(selectable)



    ##############################################
    # TIMEOUTS
    ##############################################

    def set_timeout(self, delta, handler, anchor=None, msg=None):
        """Single timeout is special case of periodic timeout"""
        return self.set_interval(delta, handler, limit=1, 
                                 anchor=anchor, msg=msg)

    def set_interval(self, delta, handler, limit=None, 
                     anchor=None, msg=None):
        """Forward to timeoutmanager, but do a thread/process
        switch so that the callback is invoked by the thread/process
        running the main loop of the scheduler."""
        tid = self._tm.set_interval(delta, 
                                    self._handle_timeout, 
                                    limit=limit, 
                                    anchor=anchor,
                                    msg=msg)
        self._timeout_pending[tid] = handler
        return tid

    def cancel_timeout(self, tid):
        """Cancel timeout"""
        if self._timeout_pending.has_key(tid):
            del self._timeout_pending[tid]
        return self._tm.cancel_timeout(tid)

    def _handle_timeout(self, info, msg):
        """Redirect timeout to timeout_queue for thread/process switch"""
        self._timeout_queue.put((info, msg))

    def _handle_timeout_queue_readable(self, selectable):
        """Redirect queued messages to correct handler based on type"""
        try:
            msg = selectable.queue.get(False)
        except Queue.Empty:
            return
        if msg != None:
            info, msg = msg
            if info != None:
                tid = info['tid']
                if self._timeout_pending.has_key(tid):
                    handler = self._timeout_pending[tid]
                    if info['last'] == True:
                        del self._timeout_pending[tid]
                    handler(info, msg)


    ##############################################
    # EXECUTION
    ##############################################

    def stop(self):
        """Request that the scheduler stops"""
        self._stop_event.set()
        self._tm.stop()

    def get_stop_event(self):
        """Return stop event used by the scheduler"""
        return self._stop_event

    def join(self, timeout=None):
        """Join timeout manager"""
        self._tm.join(timeout=timeout)

    def run(self):
        """
        Main loop
        """
        self._tm.start()
        while not self._stop_event.is_set():
            try:
                [r, w, e] = select.select(self._read_set, self._write_set, self._read_set, 1.0)
                for s in r:
                    try:
                        s.handle_readable()
                    except Exception as e:
                        self.log.exception("Exception in main loop - handle readable")
                        s.handle_error(e)
                for s in w:
                    try:
                        s.handle_writeable()
                    except Exception as e:
                        self.log.exception("Exception in main loop - handle writeable")
                        s.handle_error(e)
                for fd in e:
                    # find selectable with given fd
                    for s in self._selectables:
                        if s.fileno() == fd:
                            s.handle_error(e)

            except (select.error, socket.error)  as e:
                # Exception in select, find bad fd and remove.
                for s in self._read_set:
                    try:
                        r,w,e = select.select([s], [], [], 0)
                    except (socket.error, select.error) as e:
                        s.handle_error(e)
                for s in self._write_set:
                    try:
                        r,w,e = select.select([], [s], [], 0)
                    except (socket.error, select.error) as e:
                        s.handle_error(e)
        
        # Cleanup
        for selectable in self._selectables[:]:
            self.unregister_selectable(selectable)
            selectable.close()


        
##############################################
# SELECTABLES
##############################################

class BaseSelectable:

    """This implements a small wrapping around a socket, 
    in order to facilitate non-blocking io."""
    def __init__(self, autocleanup=False):
        self._S = None
        self._autocleanup = autocleanup
    def fileno(self):
        """Must be implemented"""
        return -1
    def close(self):
        """Close internal fd_object. Should be implemented"""
        pass
    # read set
    def enter_read_set(self):
        if not self in self._S._read_set:
            self._S._read_set.append(self)
    def leave_read_set(self):
        if self in self._S._read_set:
            self._S._read_set.remove(self)
    # write set
    def enter_write_set(self):
        if not self in self._S._write_set:
            self._S._write_set.append(self)
    def leave_write_set(self):
        if self in self._S._write_set:
            self._S._write_set.remove(self)
    # readable handler
    def set_readable_handler(self, handler):
        self._S._readable_handlers[self] = handler
    def handle_readable(self):
        if self._S._readable_handlers.has_key(self):
            self._S._readable_handlers[self](self)
    def remove_readable_handler(self):
        if self._S._readable_handlers.has_key(self):
            del self._S._readable_handlers[self]
    # writeable handler
    def set_writeable_handler(self, handler):
        self._S._writeable_handlers[self] = handler
    def handle_writeable(self):
        if self._S._writeable_handlers.has_key(self):
            self._S._writeable_handlers[self](self)
    def remove_writeable_handler(self):
        if self._S._writeable_handlers.has_key(self):
            del self._S._writeable_handlers[self]
    # error handler
    def set_error_handler(self, handler):
        self._S._error_handlers[self] = handler
    def handle_error(self, e):
        error_handler = self._S._error_handlers.get(self, None)        
        if self._autocleanup:
            self._S.unregister_selectable(self)
        if error_handler != None:
            error_handler(self, e)
    def remove_error_handler(self):
        if self._S._error_handlers.has_key(self):
            del self._S._error_handlers[self]
    # cleanup
    def cleanup(self):
        self.leave_read_set()
        self.leave_write_set()
        self.remove_readable_handler()
        self.remove_writeable_handler()
        self.remove_error_handler()


##############################################
# QUEUE SELECTABLE
##############################################

class ReadQueueSelectable(BaseSelectable):
    """This implements a selectable for 
    multiprocess queues, only read.
    """
    def __init__(self, queue, autocleanup=False):
        BaseSelectable.__init__(self, autocleanup=autocleanup)
        self.queue = queue
    def fileno(self): 
        return self.queue._reader.fileno()
    def close(self):
        self.queue.close()
        self.queue = None

class WriteQueueSelectable(BaseSelectable):
    """This implements a selectable for 
    multiprocess queues, only read.
    """
    def __init__(self, queue, autocleanup=False):
        BaseSelectable.__init__(self, autocleanup=autocleanup)
        self.queue = queue
    def fileno(self): 
        return self.queue._writer.fileno()
    def close(self):
        self.queue.close()
        self.queue = None


##############################################
# SOCKET SELECTABLE
##############################################

class SocketSelectable(BaseSelectable):
    """This implements a selectable for sockets."""    
    def __init__(self, sock, autocleanup=False):
        BaseSelectable.__init__(self, autocleanup=autocleanup)
        self.sock = sock
    def fileno(self): 
        return self.sock.fileno()
    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

##############################################
# PIPE SELECTABLE
##############################################

class PipeSelectable(BaseSelectable):
    """This implements a selectable for multiprocess pipe objects."""    
    def __init__(self, pipe, autocleanup=False):
        BaseSelectable.__init__(self, autocleanup=autocleanup)
        self.pipe = pipe
    def fileno(self): 
        return self.pipe.fileno()
    def close(self):
        if self.pipe:
            self.pipe.close()
            self.pipe = None


##############################################
# NON BLOCKING SOCKET READER
##############################################

class NonBlockingSocketReader:
    """This implements reading of descrete messages from a socket in a
    nonblocking fashion. When a selectable is readable, either zero, 1
    or more completed messages will be output through the read_handler.
    In the case of partially read messages, reading continues when the 
    selectable becomes readable again. 

    Data received from socket needs to be parsed according to
    protocol.  A data_parser must be supplied for this purpose: This
    function takes raw_data as input. It must trim away message headers
    and return the first message payload extracted from raw_data, as
    well as the remaining raw data. If given raw_data does not include a
    full message, payload should be None and remaining raw data should
    be identical to input.
    """
    def __init__(self, selectable, data_parser):
        self._data = ""
        self._read_handler = None
        self._data_parser = data_parser
        self._selectable = selectable
        self._selectable.set_readable_handler(self._handle_readable)

    def set_read_complete_handler(self, handler):
        """Define a handler for completely read messages"""
        self._read_complete_handler = handler

    def _handle_readable(self, selectable):
        """Invoked by scheduler"""
        data = ""
        try:
            data = self._selectable.sock.recv(1024)
        except socket.error as e:
            if e[0] != errno.EAGAIN:
                self._selectable.handle_error(e[0])
            return
        if data:
            # Data received
            self._data += data
            # Try to parse messages
            while True:
                payload, self._data = self._data_parser(self._data)
                if payload == None:
                    break
                if self._read_complete_handler:
                    self._read_complete_handler(self._selectable, payload)
        else:
            # Did not block, but received no data => connection closed by client.
            # Recv 0 bytes, yet fd was readable and no exception occurred
            self._selectable.handle_error(errno.EPIPE)


##############################################
# NON BLOCKING SOCKET WRITER
##############################################

class NonBlockingSocketWriter:
    """This implements writing of discrete messages to a socket in
    a nonblocking fashion. If a message is partially written, the
    socketwriter will take responsibility for completion, via the
    scheduler. In this case, the socketwriter will not accept new
    messages until the previous message is completed. A ready_handler
    is invoked when partially written messages are eventually completed.    
    """
    def __init__(self, selectable):

        self._data = None
        self._sent_bytes = 0
        self._ready_handler = None 
        self._write_complete_handler = None
        self._selectable = selectable
        self._selectable.set_writeable_handler(self._handle_writeable)

    def set_write_complete_handler(self, handler):
        self._write_complete_handler = handler

    def send_ok(self):
        return True if self._data == None else False

    def send(self, data):
        """Invoked by application"""
        if self._data != None:
            return
        self._data = data
        self._sent_bytes = 0
        return self._write()
        
    def _handle_writeable(self, selectable):
        """Invoked by scheduler"""
        completed = self._write()
        if completed:
            self._selectable.leave_write_set()
        if completed and self._write_complete_handler:            
            self._write_complete_handler()

    def _write(self):
        bytes_sent = 0
        try:
           bytes_sent = self._selectable.sock.send(self._data[self._sent_bytes:])
        except socket.error as e:
            if e[0] == errno.EAGAIN:
                self._selectable.enter_write_set()
            else:
                self._selectable.handle_error(e[0])
            return False
        if bytes_sent > 0:
            self._sent_bytes += bytes_sent
            if self._sent_bytes >= len(self._data):
                # The complete message was sent
                self._data = None
                return True
            else: 
                # Message only partially sent
                self._selectable.enter_write_set()
                return False
        else:
            # Sent 0 bytes, yet fd was writeable and no exception occurred
            # Connection closed by client
            return self._selectable.handle_error(errno.EPIPE)
