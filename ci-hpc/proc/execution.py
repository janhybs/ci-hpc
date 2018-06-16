#!/usr/bin/python
# author: Jan Hybs


import sys
import os
import subprocess


def construct(start, *rest, shell=False):
    args = start.split() if type(start) is str else start
    args.extend(rest)
    return ' '.join(args) if shell else args


def execute(*args, **kwargs):
    command = construct(*args, shell=kwargs.get('shell', False))
    cwd = kwargs.get('dir', '.')

    print('$>', construct(*args, shell=True))
    sys.stdout.flush()

    if os.path.exists(cwd):
        return subprocess.Popen(command, **kwargs, cwd=cwd)
    else:
        return subprocess.Popen(command, **kwargs)