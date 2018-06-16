#!/usr/bin/python
# author: Jan Hybs


def pick(o, default=False, *values):
    """
    Method picks first existing value from object o
    or return default if no key from given values exists in o
    :param o:
    :param default:
    :param values:
    :return:
    """
    for val in values:
        if val in o:
            return o[val]
    return default
