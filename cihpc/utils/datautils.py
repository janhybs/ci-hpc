#!/usr/bin/python
# author: Jan Hybs


import collections
from collections import defaultdict


olist = lambda x: sorted(list(set(x)))
set_if_none = lambda x, y: y if x is None else x


def recursive_get(d, attr, default=None, sep='.'):
    """
    Recursive getter with default dot separation
    :param d:
    :param attr:
    :param default:
    :param sep:
    :return:
    """
    if not isinstance(attr, str):
        return default
    if not isinstance(d, dict) or not dict:
        return default

    if sep:
        items = attr.split(sep)
    else:
        items = [attr]

    root = d
    for p in items:
        if p in root:
            root = root[p]
        else:
            return default
    return root


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
    import numpy as np

    return np.array(a).prod()**(1.0 / len(a))


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


def fillna(df):
    import pandas as pd

    return df.where(pd.notnull(df), None)


def dropzero(df):
    return df[(df != 0).all(1)]


def filter_keys(d, required=None, forbidden=None):
    if required:
        d = {k: v for k, v in d.items() if v in required}
    if forbidden:
        d = {k: v for k, v in d.items() if v not in forbidden}
    return d


def filter_values(d, required=None, forbidden=None):
    if required:
        d = {k: v for k, v in d.items() if k in required}
    if forbidden:
        d = {k: v for k, v in d.items() if k not in forbidden}
    return d


def join_lists(keys, values, format='{}={}', sep=','):
    keys = ensure_iterable(keys)
    values = ensure_iterable(values)
    return sep.join([format.format(keys[i], values[i]) for i in range(len(keys))])


def mean_confidence_interval(data, confidence=0.95, return_intervals=False):
    import numpy as np
    from scipy import stats as st

    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), st.sem(a)
    h = se * st.t.ppf((1 + confidence) / 2., n - 1)
    if return_intervals:
        return m, m - h, m + h
    return h


class xdict(defaultdict):
    def __init__(self, default=None):
        super(xdict, self).__init__(default)

    def __getitem__(self, keys):
        keys = ensure_iterable(keys)
        if len(keys) == 1:
            return super(xdict, self).__getitem__(keys[0])

        tmp = self
        for k in keys[:-1]:
            if k not in tmp:
                tmp[k] = xdict(self.default_factory)
            tmp = tmp[k]
        return tmp[keys[-1]]

    def __setitem__(self, keys, value):
        keys = ensure_iterable(keys)
        if len(keys) == 1:
            return super(xdict, self).__setitem__(keys[0], value)

        tmp = self
        for k in keys[:-1]:
            if k not in tmp:
                tmp[k] = xdict(self.default_factory)
            tmp = tmp[k]
        tmp[keys[-1]] = value


def merge_dict(*items, **items2):
    result = dict()
    for item in items:
        result.update(item)

    for k, v in items2.items():
        if k not in result:
            result[k] = dict()
        result[k].update(v)
    return result


def iter_over(iterable):
    """
    Method will iterate over given iterable and yields
    next iterable value, current index of iteration (from 0), iterable length
    :param iterable:
    :return:
    """
    current = 0
    total = len(iterable)
    for value in iterable:
        yield value, current, total
        current += 1
