#!/usr/bin/python
# author: Jan Hybs


import time


class DynamicSleep(object):
    def __init__(self, min=3.0, max=30.0, steps=10):
        if steps <= 1:
            self.steps = [max]
        else:
            step = float(max - min) / (steps - 1)
            self.steps = [min + x * step for x in range(steps)]

        self.max = max
        self._index = 0
        self._len = len(self.steps)

    def __call__(self, *args, **kwargs):
        if self._index == self._len:
            return self.max

        value = self.steps[self._index]
        self._index += 1
        return value


class Timer(object):
    def __init__(self, name=None, log=None):
        self.start_time = None
        self.stop_time = None
        self.name = name
        self.log = log

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_time = time.time()
        if self.log:
            self.log(str(self))
        return False

    @staticmethod
    def decorate(name=None, log=None):
        def real_decorator(function):
            def wrapper(*args, **kwargs):
                with Timer(name, log):
                    result = function(*args, **kwargs)
                return result

            return wrapper

        return real_decorator

    @property
    def duration(self):
        if self.stop_time and self.start_time:
            return self.stop_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0

    @property
    def micro(self):
        return self.duration * 1000.0

    @property
    def pretty_duration(self):
        return time.strftime('%H:%M:%S', time.gmtime(int(self.duration)))

    @property
    def pretty_duration_micro(self):
        micro = ('%1.3f' % (self.duration - int(self.duration)))[2:]
        return time.strftime('%H:%M:%S', time.gmtime(int(self.duration))) + '.' + micro

    def __repr__(self):
        if self.name:
            return '[{self.micro:8.2f} ms] in {self.name:20}'.format(self=self)
        return self.pretty_duration_micro
