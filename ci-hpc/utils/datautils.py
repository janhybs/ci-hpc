#!/usr/bin/python
# author: Jan Hybs


import numpy as np

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


def gmean(a):
    return np.array(a).prod()**(1.0/len(a))