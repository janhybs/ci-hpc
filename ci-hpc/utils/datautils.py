#!/usr/bin/python
# author: Jan Hybs


import numpy as np
import collections

import pandas as pd
from scipy import stats as st

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


def fillna(df):
    return df.where(pd.notnull(df), None)


def filter_keys(d, required=None, forbidden=None):
    if required:
        d = {k: v for k,v in d.items() if v in required}
    if forbidden:
        d = {k: v for k, v in d.items() if v not in forbidden}
    return d


def filter_values(d, required=None, forbidden=None):
    if required:
        d = {k: v for k,v in d.items() if k in required}
    if forbidden:
        d = {k: v for k, v in d.items() if k not in forbidden}
    return d


def join_lists(keys, values, format='{}={}', sep=','):
    keys = ensure_iterable(keys)
    values = ensure_iterable(values)
    return sep.join([format.format(keys[i], values[i]) for i in range(len(keys))])


def mean_confidence_interval(data, confidence=0.95, return_intervals=False):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), st.sem(a)
    h = se * st.t.ppf((1 + confidence) / 2., n-1)
    if return_intervals:
        return m, m-h, m+h
    return h