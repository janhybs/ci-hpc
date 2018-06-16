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


def str_presenter(dumper, data):
  if len(data.splitlines()) > 1:  # check for multiline string
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
  return dumper.represent_scalar('tag:yaml.org,2002:str', data)


def extend():
    yaml.add_constructor('!range', cpu_range)
    yaml.add_constructor('!repeat', str_repeat)
    yaml.add_representer(str, str_presenter)