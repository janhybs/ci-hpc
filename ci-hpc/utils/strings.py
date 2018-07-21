#!/usr/bin/python
# author: Jan Hybs

import random


def generate_random_key(length=8):
    """
    :type length: int
    """
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))


def pad_lines(string, pad=4):
    """
    :type pad: int or str
    :type string: str
    """
    pad_str = pad if isinstance(pad, str) else int(pad) * ' '
    return '\n'.join([pad_str + line for line in string.splitlines()])