#!/bin/python3
# author: Jan Hybs

import sys
import os


def fix_paths(verbose=False):
    # append module root directory to sys.path
    __dir__ = os.path.dirname(__file__)
    __root__ = os.path.abspath(os.path.join(__dir__, '..'))
    __tests__ = os.path.join(__root__, 'tests')
    __src__ = os.path.join(__root__, 'ci-hpc')
    sys.path = [__src__, __tests__] + sys.path
    if verbose:
        print('\n'.join(sys.path))


fix_paths()
