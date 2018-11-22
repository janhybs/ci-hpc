#!/usr/bin/python
# author: Jan Hybs


import logging
import sys
import time
import locale

if locale.getpreferredencoding().upper() != 'UTF-8':
    locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')

if str(getattr(sys.stdout, 'encoding', '')).upper() != 'UTF-8':
    # print('stdout encoding is not UTF-8, you should prepand\n'
    #       'start command with:\n'
    #       '  PYTHONIOENCODING=utf-8 python3 <your-command-here>')
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)


# from colorama import Fore, Back, Style
from cfg.config import global_configuration


if not global_configuration.tty:
    class Style:
        DIM = BRIGHT = RESET_ALL = NORMAL = ''
    class Fore:
        CYAN = WHITE = YELLOW = BLUE = GREEN = RED = ''
    class Back:
        RED = ''
else:
    from colorama import Fore, Back, Style


class ColorLevels(object):
    color_map = {
        'INFO':       Style.DIM + Fore.CYAN + 'INFO' + Style.RESET_ALL,
        'WARNING':    Style.NORMAL + Fore.YELLOW + 'WARN' + Style.RESET_ALL,
        'ERROR':      Style.BRIGHT + Back.RED + Fore.WHITE + 'ERROR' + Style.RESET_ALL,
        'FATAL':      Style.BRIGHT + Back.RED + Fore.WHITE + 'FATAL' + Style.RESET_ALL,
        'CRITICAL':   Style.BRIGHT + Back.RED + Fore.WHITE + 'CRIT' + Style.RESET_ALL,
    }
    
    @classmethod
    def get(cls, levelname):
        if global_configuration.tty:
            return cls.color_map.get(levelname, '')
        return levelname


class ExtendedFormatter(logging.Formatter):
    simple_fmt = "%(asctime)s %(threadName)+10.10s %(levelname)+4.4s: %(message)s"

    def __init__(self, padding_left=40, max_width=80, fmt=None, dateFmt=None, style='%'):
        self.left_padding = padding_left
        self.max_width = max_width

        super(ExtendedFormatter, self).__init__(fmt, dateFmt, style)

    def _pad_newlines(self, string):
        lines = string.splitlines()
        result = [lines[0]]
        padding = self.left_padding + len(logger.indent)

        # prefix = string[:self.left_padding]
        # text = string[self.left_padding:]
        for line in lines[1:]:
            result.append(' ' * padding + line)
            # len_line = len(line)
            # if len_line > (self.max_width - self.left_padding):
            #     i1 = line.rfind(' ', 0, self.max_width)
            #     i2 = line.find(' ', self.max_width, len_line)
            #     print(line)
            #     print('_' * i1 + '^')
            #     print('_' * i2 + '^')
            #     print('')
            # print(len(result))
        return '\n'.join(result)

    def format(self, record):
        return self._pad_newlines(super(ExtendedFormatter, self).format(record))


class AdditiveDateFormatter(ExtendedFormatter):
    """
    Simple Formatter which returns time relative to the last command
    output example
        ```
            $ >>> 0.0368    INFO: Processing project hello-world
            $ >>> 0.0001    INFO: processing section test
        ```
    """
    start_time = time.time()
    
    def __init__(self, fmt, datefmt=5):
        super(AdditiveDateFormatter, self).__init__(20, 80, fmt, datefmt)
    
    def format(self, record):
        result = self._fmt
        result = result.format(
            time=self.formatTime(record, self.datefmt),
            levelname=ColorLevels.get(record.levelname),
        )
        return self._pad_newlines(result % record.__dict__)
    
    def formatTime(self, record, datefmt=None):
        result = '%1.9f' % (time.time() - self.start_time)
        self.start_time = time.time()
        return result[:datefmt+1]


class RelativeDateFormatter(ExtendedFormatter):
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
        super(RelativeDateFormatter, self).__init__(17, 80, fmt, datefmt)
    
    def format(self, record):
        result = self._fmt
        result = result.format(
            time=self.formatTime(record, self.datefmt),
            levelname=ColorLevels.get(record.levelname),
        )
        return self._pad_newlines(result % record.__dict__)
    
    def formatTime(self, record, datefmt=None):
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

    LEVEL_INFO = 'info'
    LEVEL_DEBUG = 'debug'
    LEVEL_WARN = 'warn'
    LEVEL_ERROR = 'error'

    def __init__(self, logger):
        self._indent = 0
        self.logger = logger
        self.tty = None
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

    def increase_verbosity(self, amount):
        if amount:
            self.set_level('DEBUG', logger.LOGGER_ALL_HANDLERS)

    @property
    def indent(self):
        return '' if self._indent == 0 else self._indent * '--' + ' '

    def dump(self, obj, name='object', *args, skip_format=True, level='info', **kwargs):
        if self.tty:
            header = 'dumping ' + Style.BRIGHT + name + Style.RESET_ALL + ':\n'
        else:
            header = 'dumping %s: \n' % name
        try:
            import json, yaml
            obj = json.loads(json.dumps(obj))
            msg = header + yaml.dump(obj, default_flow_style=False)
        except Exception as e:
            try:
                import json, yaml
                obj = yaml.dump(obj, default_flow_style=False)
                msg = header + obj
            except:
                msg = header + str(obj)

        if skip_format:
            getattr(self.logger, level)(self.indent + msg, *args)
        else:
            getattr(self.logger, level)(self.indent + msg.format(**kwargs), *args)

    def info(self, msg, *args, skip_format=False, **kwargs):
        if skip_format:
            self.logger.info(self.indent + msg, *args)
        else:
            self.logger.info(self.indent + msg.format(**kwargs), *args)

    def debug(self, msg, *args,skip_format=False,  **kwargs):
        if skip_format:
            self.logger.debug(self.indent + msg, *args)
        else:
            self.logger.debug(self.indent + msg.format(**kwargs), *args)

    def warn(self, msg, *args, skip_format=False, **kwargs):
        if skip_format:
            self.logger.warning(self.indent + msg, *args)
        else:
            self.logger.warning(self.indent + msg.format(**kwargs), *args)

    def error(self, msg, *args, skip_format=False, **kwargs):
        if skip_format:
            self.logger.error(self.indent + msg, *args)
        else:
            self.logger.error(self.indent + msg.format(**kwargs), *args)

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
    def init(cls, log_path=None, log_style=None, use_tty=None):
        """
        :rtype: Logger
        """
        logger = logging.getLogger('root')

        file_log = logging.FileHandler(log_path, encoding='utf-8')
        stream_log = logging.StreamHandler(sys.stdout)
        file_formatter = ExtendedFormatter(fmt=ExtendedFormatter.simple_fmt)

        if log_style == 'short':
            stream_formatter = RelativeDateFormatter(''.join([
                    Fore.BLUE + Style.BRIGHT + '>>> ' + Style.RESET_ALL,
                    Style.DIM + '{time} ' + Style.RESET_ALL,
                    '{levelname}',
                    ": %(message)s"
                ])
            )
        else:
            stream_formatter = ExtendedFormatter(fmt=ExtendedFormatter.simple_fmt)

        logger.setLevel(logging.DEBUG)
        file_log.setLevel(logging.DEBUG)
        stream_log.setLevel(logging.DEBUG)

        file_log.setFormatter(file_formatter)
        stream_log.setFormatter(stream_formatter)

        logger.addHandler(file_log)
        logger.addHandler(stream_log)

        logger = Logger(logger)
        logger.tty = getattr(sys.stdout, 'isatty', lambda: False)() or use_tty
        return logger


logger = None  # type: Logger
# logger.info('\n' + '-' * 80)
