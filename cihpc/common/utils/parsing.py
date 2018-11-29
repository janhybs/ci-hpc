#!/usr/bin/python3
# author: Jan Hybs

import argparse
from collections import defaultdict


class RawFormatter(argparse.HelpFormatter):
    """
    Class SmartFormatter prints help messages without any formatting
        or unwanted line breaks, acivated when help starts with R|
    """

    def _split_lines(self, text, width):
        if text.startswith('R|\n'):
            text = text[3:].rstrip()
            lines = text.splitlines()
            first_indent = len(lines[0]) - len(lines[0].lstrip())
            return [l[first_indent:] for l in lines]
        elif text.startswith('R|'):
            return [l.lstrip() for l in text[2:].strip().splitlines()]

        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


def defaultdict_type(items, default_value='', default_name='', separator=':'):
    """
    Convert list to dict
    Example:
        list ["key:value", "key2:value2", ...] to dict {key:value, key2:value2}
    :param items:
    :param default_value:
    :param default_name:
    :param separator:
    :return:
    """
    result = dict()
    if items:
        for item in items:
            split = item.split(separator, 1)
            # no name provided
            if len(split) == 1:
                result[default_name] = split[0]
            else:
                result[split[0]] = split[1]

    return defaultdict(lambda: default_value, **result)

    # args.git_branch = dict(tuple(d.split(':', 1)) for d in args.git_branch)
    # args.git_branch = defaultdict(lambda: 'master', **args.git_branch)


def convert_project_arguments(namespace, excludes=None):
    args = vars(namespace)
    result = list()
    base_args = ['project', 'git-url', 'config-dir', 'pbs', 'timeout', 'check-interval', 'log-path', 'log-style']
    bool_args = ['verbosity', 'tty']
    extra_args = ['git-commit', 'git-branch']
    rest_args = ['step']

    for key, value in args.items():
        key = key.replace('_', '-')

        if excludes and key in excludes:
            continue

        if key in base_args and value is not None:
            result.append('--' + key)
            result.append(str(value))

        elif key in bool_args and value:
            result.append('--' + key)

        elif key in extra_args and value:
            for k, v in value.items():
                if v:
                    result.append('--' + key)
                    result.append('%s:%s' % (str(k), str(v)))
        elif key in rest_args:
            result.extend(value)
    return result
