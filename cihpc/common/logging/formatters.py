#!/bin/python3
# author: Jan Hybs

import logging


class SmartLoggerFormatter(logging.Formatter):
    """Formatter class which aligns messages with newlines properly and default style uses relative msec time"""
    default_format = '{asctime}:{threadName}:{name}:{levelname}:#{message}'

    def __init__(self, fmt=None, min_chars=40):
        super(SmartLoggerFormatter, self).__init__(
            fmt or self.default_format,
            datefmt='%Y-%m-%d.%H:%M:%S',
            style='{'
        )
        self._min_chars = min_chars

    def format(self, record):

        if record.threadName == 'MainThread':
            record.threadName = 'MT'
        if str(record.threadName).startswith('Thread-'):
            record.threadName = 'T' + str(record.threadName)[7:]

        if str(record.name).startswith('cihpc.'):
            record.name = str(record.name)[6:]

        record.relativeCreatedSec = ('%1.6f' % (record.relativeCreated / 1000.0))[0:5]

        result = super(SmartLoggerFormatter, self).format(record)

        index = result.find('#')
        if 10 < index < 100:
            new_result = ('{:%ds}' % self._min_chars).format(result[:index]) + ' '
            lines = result[index+1:].splitlines()
            return new_result + ('\n' + ' ' * max(index+1, self._min_chars+1)).join(lines)


class RelativeLoggerFormatter(SmartLoggerFormatter):
    """Formatter class which aligns messages with newlines properly"""
    default_format = '{relativeCreatedSec}:{threadName}:{name}:{levelname}:#{message}'

    def __init__(self, fmt=None, min_chars=40):
        super(RelativeLoggerFormatter, self).__init__(
            fmt or self.default_format,
            min_chars
        )
