#!/usr/bin/python
# author: Jan Hybs

import os
import sys

__dir__ = os.path.abspath(os.path.dirname(__file__))
__root__ = os.path.dirname(os.path.dirname(__dir__))

__cfg__ = os.path.join(__root__, 'cfg')
__src__ = os.path.join(__root__, 'ci-hpc')


class global_configuration(object):
    tty = getattr(sys.stdout, 'isatty', lambda: False)()
    root = __root__
    cfg = __cfg__
    src = __src__
    log_path = os.path.join(__root__, 'ci-hpc.log')
    cfg_path = os.path.join(__cfg__, 'secret.yaml')
