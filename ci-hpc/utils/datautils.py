#!/usr/bin/python
# author: Jan Hybs


import numpy as np
import collections

olist = lambda x: sorted(list(set(x)))
set_if_none = lambda x,y: y if x is None else x


def filter_rows(data, **rules):
    subdata = data.copy()
    for k, v in rules.items():
        if k.startswith('_'):
            k = k[1:].replace('_', '-')
        if v is not None:
            if type(v) is list:
                subdata = subdata[subdata[k].isin(v)]
            else:
                subdata = subdata[subdata[k] == v]
    return subdata


def flatten(d, parent_key='', sep='-'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def gmean(a):
    return np.array(a).prod()**(1.0/len(a))


def ensure_iterable(inst):
    """
    Wraps scalars or string types as a list, or returns the iterable instance.
    """
    if isinstance(inst, str):
        return [inst]
    elif not isinstance(inst, collections.Iterable):
        return [inst]
    else:
        return inst


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__