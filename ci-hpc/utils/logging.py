#!/usr/bin/python
# author: Jan Hybs


import logging
import sys


class Logger(object):
    """
    Singleton class for logging
    :type logger: utils.Logger
    """
    def __init__(self, logger):
        self._indent = 0
        self.logger = logger

        self.debug_exception = self._exception('debug')
        self.info_exception = self._exception('info')
        self.warn_exception = self._exception('warn')
        self.error_exception = self._exception('error')

        self.exception = self.warn_exception

    def info(self, msg, *args, skip_format=False, **kwargs):
        indent = '' if self._indent == 0 else self._indent * '--' + ' '
        if skip_format:
            self.logger.info(indent + msg, *args)
        else:
            self.logger.info(indent + msg.format(**kwargs), *args)

    def debug(self, msg, *args,skip_format=False,  **kwargs):
        indent = '' if self._indent == 0 else self._indent * '--' + ' '
        if skip_format:
            self.logger.debug(indent + msg, *args)
        else:
            self.logger.debug(indent + msg.format(**kwargs), *args)

    def warn(self, msg, *args, skip_format=False, **kwargs):
        indent = '' if self._indent == 0 else self._indent * '--' + ' '
        if skip_format:
            self.logger.warning(indent + msg, *args)
        else:
            self.logger.warning(indent + msg.format(**kwargs), *args)

    def error(self, msg, *args, skip_format=False, **kwargs):
        indent = '' if self._indent == 0 else self._indent * '--' + ' '
        if skip_format:
            self.logger.error(indent + msg, *args)
        else:
            self.logger.error(indent + msg.format(**kwargs), *args)

    def _exception(self, method='warn'):
        def exc(msg, *args, **kwargs):
            return getattr(self.logger, method)(msg, *args, exc_info=True, **kwargs)
        return exc

    def open(self):
        self._indent += 1

    def exit(self):
        self._indent -= 1

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit()
        return False
    
    warning = warn

    @classmethod
    def init(cls, log_dir=None):
        """
        :rtype: Logger
        """
        from os.path import abspath, join, dirname

        if not log_dir:
            log_dir = abspath(join(dirname(__file__), '../' * 2))

        logger = logging.getLogger('root')

        file_log = logging.FileHandler(join(log_dir, 'ci-hpc.log'))
        stream_log = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s [%(threadName)-10.10s] %(levelname)+8.8s: %(message)s")

        logger.setLevel(logging.DEBUG)
        file_log.setLevel(logging.DEBUG)
        stream_log.setLevel(logging.DEBUG)

        file_log.setFormatter(formatter)
        stream_log.setFormatter(formatter)

        logger.addHandler(file_log)
        logger.addHandler(stream_log)

        logger = Logger(logger)
        return logger


logger = Logger.init()
logger.info('initialized logger instance \n' + '-' * 80)
