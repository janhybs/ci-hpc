#!/bin/python3
# author: Jan Hybs

import yaml


def cpu_range(loader, node):
    value = loader.construct_scalar(node)
    values = list(range(*map(int, value.split(' '))))
    return values


def str_repeat(loader, node):
    value = loader.construct_scalar(node)
    s, repeat = value.split(' ')
    return int(repeat) * s


def extend():
    yaml.add_constructor('!range', cpu_range)
    yaml.add_constructor('!repeat', str_repeat)