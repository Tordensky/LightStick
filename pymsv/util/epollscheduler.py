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
from util.mylog import *

ERROR_MASK = select.EPOLLHUP | select.EPOLLERR

LOG_RAW_DATA = False

##############################################
# DEBUG - log incoming data
##############################################
def log_data(addr, data):
    """
    Log to /tmp/msv/hostname_port.log
    """
    path = "/tmp/msv/%s_%s.log"%(addr[0], addr[1])
    import os
    if not os.path.exists("/tmp/msv"):
        os.makedirs("/tmp/msv/")
    f = open(path, "ab+")
    f.write(data)
    f.close()

##############################################
# SCHEDULER
##############################################

class Scheduler:

    def __init__(self,  name, stop_event=None):
        
        self._name = name

        # Execution
        self._stop_event = stop_event if stop_event != None else multiprocessing.Event()

        # IO
        self._selectables =  {} # fd -> selectable
        self._epoll_masks = {} # fd -> mask
        self._epoll = select.epoll()

        # Timeouts
        self._tm = timeouts.TimeoutManager(stop_event=self._stop_event)
        self._timeout_pending = {} # tid -> handler

        # Timeout Queue
        self._timeout_queue = multiprocessing.Queue()
        s = ReadQueueSelectable(self._timeout_queue)
        self.register_selectable(s)
        s.set_readable_handler(self._handle_timeout_queue_readable)
        s.enter_read_set()

        # Log
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
        fd = selectable.fileno()
        if self._selectables.has_key(fd):
            return
        selectable._S = self
        self._selectables[fd] = selectable
        # Define default eventmask
        eventmask = ERROR_MASK # TODO add - EPOLLET?
        self._epoll_masks[fd] = eventmask
        self._epoll.register(fd, eventmask) 

    def count_selectables(self):
        """Return number of registrered selectables"""
        return len(self._selectables)

    def unregister_selectable(self, selectable):
        """
        Remove a selectable from the scheduler
        """
        fd = selectable.fileno()
        selectable.cleanup()
        if self._selectables.has_key(fd):
            del self._selectables[fd]
            del self._epoll_masks[fd]
            self._epoll.unregister(fd)

    ##############################################
    # READ, WRITE and ERROR
    ##############################################

    def _epoll_add_to_mask(self, selectable, mask):
        """Makes sure bits specified in mask are set in epoll event mask"""
        fd = selectable.fileno()
        if self._selectables.has_key(fd):
            oldmask = self._epoll_masks.get(fd, 0)
            newmask = oldmask | mask
            if (newmask != oldmask):
                self._epoll_masks[fd] = newmask
                self._epoll.modify(fd, newmask)

    def _epoll_remove_from_mask(self, selectable, mask):
        """Makes sure bits specified in mask are removed in epoll event mask"""
        fd = selectable.fileno()
        if self._selectables.has_key(fd):
            oldmask = self._epoll_masks.get(fd, 0)
            newmask = oldmask & ~mask
            if (newmask != oldmask):
                self._epoll_masks[fd] = newmask
                self._epoll.modify(fd, newmask)

    def enter_read_set(self, selectable):
        self._epoll_add_to_mask(selectable, select.EPOLLIN)

    def leave_read_set(self, selectable):
        self._epoll_remove_from_mask(selectable, select.EPOLLIN)

    def enter_write_set(self, selectable):
        self._epoll_add_to_mask(selectable, select.EPOLLOUT)

    def leave_write_set(self, selectable):
        self._epoll_remove_from_mask(selectable, select.EPOLLOUT)


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
        try:
            while not self._stop_event.is_set():
                events = self._epoll.poll(1.0)               
                for fd, event in events:
                    s = self._selectables.get(fd, None)
                    if s == None:
                        continue
                    error = False

                    if event & select.EPOLLIN:
                        try:
                            s.handle_readable()
                        except Exception as e:
                            error = e
                            self.log.exception("Exception in main loop - handle readable")

                    if event & select.EPOLLOUT:
                        try:
                            s.handle_writeable()
                        except Exception as e:
                            error = e
                            self.log.exception("Exception in main loop - handle writeable")
                            
                    if (event & ERROR_MASK) or error:
                        try:
                            s.handle_error(error)
                        except Exception as e:
                            print "error handle error", e
                            traceback.print_exc()
                        finally:
                            self.unregister_selectable(s)


        finally:
            # Cleanup and close
            self._tm.stop()          
            for selectable in self._selectables.values()[:]:
                self.unregister_selectable(selectable)
                selectable.close()
            self._epoll.close()

        
##############################################
# SELECTABLES
##############################################


class BaseSelectable:

    """This implements a small wrapping around a socket, 
    in order to facilitate non-blocking io."""
    def __init__(self, autocleanup=False):
        self._S = None
        self._readable_handler = None
        self._writeable_handler = None
        self._error_handler = None
        self._autocleanup = autocleanup
    def fileno(self):
        """Must be implemented"""
        return -1
    def close(self):
        """Close internal fd_object. Should be implemented"""
        pass
    # read set
    def enter_read_set(self):
        self._S.enter_read_set(self)
    def leave_read_set(self):
        self._S.leave_read_set(self)
    # write set
    def enter_write_set(self):
        self._S.enter_write_set(self)
    def leave_write_set(self):
        self._S.leave_write_set(self)
    # readable handler
    def set_readable_handler(self, handler):
        self._readable_handler = handler
    def handle_readable(self):
        if self._readable_handler:
            self._readable_handler(self)
    def remove_readable_handler(self):
        self._readable_handler = None
    # writeable handler
    def set_writeable_handler(self, handler):
        self._writeable_handler = handler
    def handle_writeable(self):
        if self._writeable_handler:
            self._writeable_handler(self)
    def remove_writeable_handler(self):
        self._writeable_handler = None
    # error handler
    def set_error_handler(self, handler):
        self._error_handler = handler
    def handle_error(self, e):
        error_handler = self._error_handler
        if self._autocleanup:
            self._S.unregister_selectable(self)
        if error_handler != None:
            error_handler(self, e)
    def remove_error_handler(self):
        self._error_handler = None

    # cleanup
    def cleanup(self):
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
        self._fd = self.queue._reader.fileno()
    def fileno(self): 
        return self._fd
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
        self._fd = self.queue._writer.fileno() 
    def fileno(self): 
        return self._fd
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
        self._fd = self.sock.fileno() 
    def fileno(self): 
        return self._fd
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
        self._fd = self.pipe.fileno() 
    def fileno(self): 
        return self._fd
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
            # DEBUG LOGGING
            if LOG_RAW_DATA:
                log_data(self._selectable.sock.getpeername(), data)
            #/DEBUG

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
                    self.log.warning("Got message but don't have a read_complete_handler")
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
