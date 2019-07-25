#!/bin/python3
# author: Jan Hybs
import enum


class OnError(enum.Enum):
    BREAK = 'break'
    CONTINUE = 'continue'
    EXIT = 'exit'


class ExecError(Exception):
    """
    :type reason: str
    :type on_error: OnError
    :type details: dict
    """

    EXECUTION_FAILED = 'execution failed'

    def __init__(self, reason, on_error, details=None):
        self.reason = reason
        self.on_error = on_error
        self.details = details
