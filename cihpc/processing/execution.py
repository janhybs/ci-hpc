#!/usr/bin/python
# author: Jan Hybs

import os
import subprocess
import sys


def construct(start, *rest, shell=False):
    args = start.split() if type(start) is str else start
    args.extend(rest)
    return ' '.join(args) if shell else args


def create_execute_command(logger_method, stdout):
    def execute(*args, **kwargs):
        command = construct(*args, shell=kwargs.get('shell', False))
        cwd = kwargs.pop('dir', '.')

        logger_method('$> %s', construct(*args, shell=True))
        sys.stdout.flush()

        if os.path.exists(cwd):
            return subprocess.Popen(command, **kwargs, cwd=cwd, stdout=stdout, stderr=subprocess.STDOUT)
        else:
            return subprocess.Popen(command, **kwargs, stdout=stdout, stderr=subprocess.STDOUT)

    return execute
