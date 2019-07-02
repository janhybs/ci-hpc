#!/usr/bin/python
# author: Jan Hybs

from loguru import logger
import subprocess as sp
from time import time

from cihpc.common.utils.files.dynamic_io import DynamicIO


class ProcessStepResult(object):
    """
    :type process: subprocess.Popen
    :type output:  str
    """

    def __init__(self):
        self.process = None
        self.duration = None
        self.shell_duration = None
        self.returncode = None
        self.start_time = None
        self.end_time = None

        self.output = None
        self.error = None

    def __enter__(self):
        self.start_time = time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time()
        self.duration = self.end_time - self.start_time
        return False

    def __repr__(self):
        return 'ProcessStepResult({self.process}, {self.duration})'.format(self=self)

    def to_json(self):
        return dict(
            start_time=self.start_time,
            end_time=self.end_time,
            returncode=self.returncode,
            duration=self.duration,
            output=self.output,
            error=self.error,
            shell_duration=self.shell_duration,
        )


def process_popen(worker):
    """
    :type worker: cihpc.common.processing.pool.Worker
    :return:
    """
    crate = worker.crate
    io = DynamicIO(crate.output)
    result = ProcessStepResult()
    with io as fp:
        process = sp.Popen(crate.args, stdout=fp, stderr=sp.STDOUT)

        result.process = process
        with result:
            result.returncode = process.wait()
            if result.returncode == 0:
                logger.debug('ok [%d] ended with %d' % (process.pid, result.returncode))
            else:
                logger.warning('process [%d] ended with %d' % (process.pid, result.returncode))

    # try to grab output
    result.output = getattr(io.opener, 'output', None)
    return result
