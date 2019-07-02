#!/bin/python3
# author: Jan Hybs
import os
import subprocess
import sys
import threading
from time import monotonic as _time


def construct(start, *rest, shell=False):
    args = start.split() if type(start) is str else start
    args.extend(rest)
    return ' '.join(args) if shell else args


def create_execute_command(logger_method, stdout):
    def execute(*args, **kwargs):
        command = construct(*args, shell=kwargs.get('shell', False))
        cwd = kwargs.pop('dir', '.')

        logger_method('$> %s', construct(*args, shell=True))
        sys.stdout.flush()

        if os.path.exists(cwd):
            return subprocess.Popen(command, **kwargs, cwd=cwd, stdout=stdout, stderr=subprocess.STDOUT)
        else:
            return subprocess.Popen(command, **kwargs, stdout=stdout, stderr=subprocess.STDOUT)

    return execute


class ComplexSemaphore(object):
    """This class implements semaphore objects.

    Semaphores manage a counter representing the number of release() calls minus
    the number of acquire() calls, plus an initial value. The acquire() method
    blocks if necessary until it can return without making the counter
    negative. If not given, value defaults to 1.

    """

    # After Tim Peters' semaphore class, but not quite the same (no maximum)

    def __init__(self, value=1):
        if value < 0:
            raise ValueError("semaphore initial value must be >= 0")
        self._cond = threading.Condition(threading.Lock())
        self._value = value
        self._limit = value

    @property
    def value(self):
        return self._value

    @property
    def limit(self):
        return self._limit

    def acquire(self, blocking=True, timeout=None, value=1):
        """Acquire a semaphore, decrementing the internal counter by one.

        When invoked without arguments: if the internal counter is larger than
        zero on entry, decrement it by one and return immediately. If it is zero
        on entry, block, waiting until some other thread has called release() to
        make it larger than zero. This is done with proper interlocking so that
        if multiple acquire() calls are blocked, release() will wake exactly one
        of them up. The implementation may pick one at random, so the order in
        which blocked threads are awakened should not be relied on. There is no
        return value in this case.

        When invoked with blocking set to true, do the same thing as when called
        without arguments, and return true.

        When invoked with blocking set to false, do not block. If a call without
        an argument would block, return false immediately; otherwise, do the
        same thing as when called without arguments, and return true.

        When invoked with a timeout other than None, it will block for at
        most timeout seconds.  If acquire does not complete successfully in
        that interval, return false.  Return true otherwise.

        The value parameter specifies how many units to take from the semaphore
        default value is 1.

        """
        if not blocking and timeout is not None:
            raise ValueError("can't specify timeout for non-blocking acquire")

        if value > self._limit:
            raise ValueError("can't aquire the lock because specified value is greater then max value")

        rc = False
        endtime = None
        with self._cond:
            while self._value < value:
                if not blocking:
                    break
                if timeout is not None:
                    if endtime is None:
                        endtime = _time() + timeout
                    else:
                        timeout = endtime - _time()
                        if timeout <= 0:
                            break
                self._cond.wait(timeout)
            else:
                self._value -= value
                rc = True
        return rc

    __enter__ = acquire

    def release(self, value=1):
        """Release a semaphore, incrementing the internal counter by one.

        When the counter is zero on entry and another thread is waiting for it
        to become larger than zero again, wake up that thread.

        """
        with self._cond:
            self._value += value
            self._cond.notify()

    def __exit__(self, t, v, tb):
        self.release()