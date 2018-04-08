#!/bin/python3
# author: Jan Hybs

import os
import yaml
import utils.extend_yaml
utils.extend_yaml.extend()


def yaml_dump(obj):
    return yaml.dump(obj, default_flow_style=False)


def yaml_load(s):
    return yaml.load(s)


def read_file(path, default=''):
    if os.path.exists(path):
        with open(path, 'r') as fp:
            return fp.read()
    else:
        return default


def load_config(path, replace=True):
    return yaml_load(read_file(path, default='{}'))


def configure_file(path, variables, convert=yaml_load):
    content = read_file(path)
    for k, v in variables.items():
        content = content.replace('@%s@' % k, v)

    return convert(content)
