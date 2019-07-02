#!/bin/python3
# author: Jan Hybs

import yaml
import os


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


def read_file(loader, node):
    from cihpc.cfg.config import global_configuration

    cwd = global_configuration.project_cfg_dir
    path = node.value

    with open(os.path.join(cwd, path), 'r') as fp:
        return fp.read()


def read_yaml(loader, node):
    from cihpc.cfg.config import global_configuration

    cwd = global_configuration.project_cfg_dir
    path = node.value

    with open(os.path.join(cwd, path), 'r') as fp:
        return yaml.safe_load(fp)


def extend():
    yaml.add_constructor('!range', cpu_range, Loader=yaml.SafeLoader)
    yaml.add_constructor('!repeat', str_repeat, Loader=yaml.SafeLoader)
    yaml.add_constructor('!readfile', read_file, Loader=yaml.SafeLoader)
    yaml.add_constructor('!readyaml', read_yaml, Loader=yaml.SafeLoader)
    yaml.add_representer(str, str_presenter, Dumper=yaml.SafeDumper)
