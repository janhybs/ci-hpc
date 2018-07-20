#!/usr/bin/python
# author: Jan Hybs


import logging
import sys
import time

from colorama import Fore, Back, Style


class ColorLevels(object):
    isatty = sys.stdout.isatty()
    color_map = {
        'INFO':       Style.DIM + Fore.CYAN,
        'WARNING':    Style.NORMAL + Fore.YELLOW,
        'ERROR':      Style.BRIGHT + Back.RED + Fore.WHITE,
        'ERROR':      Style.BRIGHT + Back.RED + Fore.WHITE,
        'CRITICAL':   Style.BRIGHT + Back.RED + Fore.WHITE,
    }
    
    @classmethod
    def get(cls, levelname):
        if cls.isatty:
            return cls.color_map.get(levelname, '') + levelname + Style.RESET_ALL
        return levelname
        

class AdditiveDateFormatter(logging.Formatter):
    """
    Simple Formatter which returns time relative to the last command
    output example
        ```
            >>> 0.0368    INFO: Processing project hello-world
            >>> 0.0001    INFO: processing section test
        ```
    """
    start_time = time.time()
    
    def __init__(self, fmt, datefmt=5):
        super(AdditiveDateFormatter, self).__init__(fmt, datefmt)
    
    def format(self, record):
        result = self._fmt
        result = result.format(
            time=self.formatTime(record, self.datefmt),
            levelname=ColorLevels.get(record.levelname),
        )
        return result % record.__dict__
    
    def formatTime(self, record, datefmt):
        result = '%1.9f' % (time.time() - self.start_time)
        self.start_time = time.time()
        return result[:datefmt+1]
        
class RelativeDateFormatter(logging.Formatter):
    """
    Simple Formatter which returns time relative since the start of the logger
    output example
        ```
            >>> 0.0368    INFO: Processing project hello-world
            >>> 0.0369    INFO: processing section test
        ```
    """
    start_time = time.time()
    
    def __init__(self, fmt, datefmt=6):
        super(RelativeDateFormatter, self).__init__(fmt, datefmt)
    
    def format(self, record):
        result = self._fmt
        result = result.format(
            time=self.formatTime(record, self.datefmt),
            levelname=ColorLevels.get(record.levelname),
        )
        return result % record.__dict__
    
    def formatTime(self, record, datefmt):
        result = '%1.9f' % (time.time() - self.start_time)
        return result[:datefmt]

class Logger(object):
    """
    Singleton class for logging
    :type logger: utils.Logger
    """
    
    LOGGER_FILEHANDLER = 0
    LOGGER_STREAMHANDLER = 1
    LOGGER_ALL_HANDLERS = -1
    
    def __init__(self, logger):
        self._indent = 0
        self.logger = logger
        self.file_handler = self.logger.handlers[0]
        self.stream_handler = self.logger.handlers[1]
        self.log_file = self.file_handler.baseFilename

        self.debug_exception = self._exception('debug')
        self.info_exception = self._exception('info')
        self.warn_exception = self._exception('warn')
        self.error_exception = self._exception('error')

        self.exception = self.warn_exception
    
    def set_level(self, level, logger=-1):
        if logger == self.LOGGER_ALL_HANDLERS:
            loggers = [0, 1]
        else:
            loggers = [logger]
        
        level = level if type(level) is int else getattr(logging, level.upper())
        for l in loggers:
            self.logger.handlers[l].setLevel(level)
        return self.logger.handlers

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
        file_formatter = logging.Formatter("%(asctime)s %(levelname)+8.8s: %(message)s")
        
        if sys.stdout.isatty():
            stream_formatter = RelativeDateFormatter(''.join([
                    Fore.BLUE + Style.BRIGHT + '>>> ' + Style.RESET_ALL,
                    Style.DIM + '{time} ' + Style.RESET_ALL,
                    Fore.GREEN + Style.DIM + '{levelname}' + Style.RESET_ALL,
                    ": %(message)s"
                ])
            )
        else:
            stream_formatter = logging.Formatter("%(asctime)s %(levelname)+8.8s: %(message)s")

        logger.setLevel(logging.DEBUG)
        file_log.setLevel(logging.DEBUG)
        stream_log.setLevel(logging.DEBUG)

        file_log.setFormatter(file_formatter)
        stream_log.setFormatter(stream_formatter)

        logger.addHandler(file_log)
        logger.addHandler(stream_log)

        logger = Logger(logger)
        return logger


logger = Logger.init()
# logger.info('\n' + '-' * 80)
