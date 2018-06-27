#!/usr/bin/python
# author: Jan Hybs

import random


def generate_random_key(length):
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))