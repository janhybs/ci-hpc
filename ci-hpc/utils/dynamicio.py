#!/usr/bin/python
# author: Jan Hybs


class DynamicIO(object):
    """
    Simple class which returns valid file pointer while opening file
    if no location is passed, returns None
    """
    def __init__(self, location, mode='a'):
        self.stdout = not isinstance(location, str)
        self.location = location
        self.mode = mode
        self._fp = None

    def __enter__(self):
        if self.stdout:
            self._fp = None
            return self._fp

        self._fp = open(self.location, self.mode)
        return self._fp

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stdout:
            return False

        self._fp.close()
        self._fp = None
        return False

    @property
    def fp(self):
        """
        :rtype: typing.TextIO
        """
        return self._fp

