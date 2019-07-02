#!/bin/python3
# author: Jan Hybs

import enum
import subprocess


class StdoutType(enum.Enum):
    NONE = None
    DEVNULL = subprocess.DEVNULL
    PIPE = subprocess.PIPE
