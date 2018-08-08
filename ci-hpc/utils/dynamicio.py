#!/usr/bin/python
# author: Jan Hybs

from utils.glob import global_configuration
from utils.logging import logger
import tempfile
import os
import subprocess


class Opener(object):
    def __init__(self, location, mode):
        self.location = location
        self.mode = mode
        self.fp = None

    def open(self):
        return None

    def close(self):
        return None


class OpenerStdout(Opener):
    pass


class OpenerLog(Opener):
    def open(self):
        self.fp = open(global_configuration.log_path, self.mode)
        return self.fp

    def close(self):
        self.fp.close()
        return None


class OpenerNull(Opener):
    def open(self):
        return subprocess.DEVNULL

    def close(self):
        return subprocess.DEVNULL


class OpenerFile(Opener):
    def open(self):
        self.fp = open(self.location, self.mode)
        return self.fp

    def close(self):
        self.fp.close()
        return None


class OpenerBoth(Opener):
    def __init__(self, location, mode):
        super(OpenerBoth, self).__init__(location, mode)
        self.tf = None
        self.output = None

    def open(self):
        fd, self.tf = tempfile.mkstemp()
        self.fp = os.fdopen(fd, 'w')
        return self.fp

    def close(self):
        self.fp.close()
        with open(self.tf, 'r') as fp:
            self.output = fp.read()
            logger.info('content: \n%s', self.output)
        os.unlink(self.tf)
        return None


class DynamicIO(object):
    """
    Simple class which returns valid file pointer while opening file
    if no location is passed, returns None
    :type fp: typing.TextIO
    """
    TYPES = {
        'stdout': OpenerStdout,
        'log': OpenerLog,
        'log+stdout': OpenerBoth,
        'stdout+log': OpenerBoth,
        'null': OpenerNull,
    }

    def __init__(self, location, mode='a'):
        self.location = location
        self.mode = mode
        self.opener = self.TYPES.get(self.location, OpenerFile)(self.location, self.mode)
        self.fp = None

    def __enter__(self):
        self.fp = self.opener.open()
        return self.fp

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.opener.close()
        return False

