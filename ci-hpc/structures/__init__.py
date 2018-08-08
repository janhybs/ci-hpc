#!/usr/bin/python
# author: Jan Hybs


def new(o, key, cls):
    """
    Method will construct given class if key exists in a object
    or return None
    :param o: object from which key is extracted
    :param key: name of the filed which is tested and extracted later on
    :param cls: cls which is constructed
    :return:
    """
    if key in o:
        if isinstance(o[key], dict):
            return cls(**o[key])
        return cls(o[key])
    return None


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
