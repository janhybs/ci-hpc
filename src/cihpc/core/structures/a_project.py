#!/bin/python3
# author: Jan Hybs


class ComplexClass(object):
    def __init__(self, kwargs):
        self._enabled = bool(kwargs)

    def __bool__(self):
        return self._enabled

    def __repr__(self):
        return '{self._enable_str}{self.__class__.__name__}'.format(self=self)

    @property
    def _enable_str(self):
        return '[T]' if self else '[F]'
