#!/usr/bin/python
# author: Jan Hybs


import time


class Timer(object):
    def __init__(self, name=None):
        self.start_time = None
        self.stop_time = None
        self.name = name

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_time = time.time()
        return False

    @property
    def duration(self):
        if self.stop_time:
            return self.stop_time - self.start_time
        else:
            return time.time() - self.start_time

    @property
    def pretty_duration(self):
        return time.strftime('%H:%M:%S', time.gmtime(int(self.duration)))

    @property
    def pretty_duration_micro(self):
        micro = ('%1.3f' % (self.duration - int(self.duration)))[2:]
        return time.strftime('%H:%M:%S', time.gmtime(int(self.duration))) + '.' + micro