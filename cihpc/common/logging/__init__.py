#!/bin/python3
# author: Jan Hybs


import sys
import logging


class LogConfig(object):
    stream_handler: logging.StreamHandler = None
    file_handler: logging.FileHandler = None

    log_level: int = None
    file_level: int = None
    stream_level: int = None

    log_path: str = None
    stream: any = None


def basic_config(level=logging.INFO, log_path='.ci-hpc.log', stream=sys.stdout, file_level=None, stream_level=None):
    """
    shortcut method for initializing logging

    Parameters
    ----------
    level: int
        default level for all the handlers
    log_path: str
        location of the log file where logs will be written
    stream: stream
        sys.stdout, sys.stderr or any other file-like stream implementation
    file_level: int
        level specific to the file_handler
    stream_level: int
        level specific to the stream_handler

    Returns
    -------

    """
    from cihpc.common.logging.formatters import (
        RelativeLoggerFormatter, SmartLoggerFormatter
    )

    LogConfig.level = level
    LogConfig.file_level = file_level or LogConfig.level
    LogConfig.stream_level = stream_level or LogConfig.level

    LogConfig.log_path = log_path
    LogConfig.stream = stream

    handlers = []

    if LogConfig.stream:
        LogConfig.stream_handler = logging.StreamHandler(LogConfig.stream)
        LogConfig.stream_handler.setFormatter(RelativeLoggerFormatter())
        handlers.append(LogConfig.stream_handler)

    if LogConfig.log_path:
        LogConfig.file_handler = logging.FileHandler(LogConfig.log_path)
        LogConfig.file_handler.setFormatter(SmartLoggerFormatter())
        handlers.append(LogConfig.file_handler)

    logging.basicConfig(
        level=LogConfig.level,
        handlers=handlers
    )

    if LogConfig.stream_handler and LogConfig.stream_level != LogConfig.level:
        LogConfig.stream_handler.setLevel(LogConfig.stream_level)

    if LogConfig.file_handler and LogConfig.file_level != LogConfig.level:
        LogConfig.file_handler.setLevel(LogConfig.file_level)

    return LogConfig
