#!/bin/python3
# author: Jan Hybs
from collections import defaultdict
from importlib import reload
from cihpc.cfg.config import global_configuration
from cihpc.core.db import CIHPCMongo

import pandas as pd
import numpy as np
import scipy as sc

from matplotlib import pyplot as plt
import seaborn as sea

from IPython.core.display import display, HTML
display(HTML("<style>.container { width: 75% !important; } .rendered_htmlm {max-width: 850px;}</style>"))


global_configuration.cfg_secret_path = '/home/jan-hybs/projects/ci-hpc/cfg/secret.yaml'
mongo = CIHPCMongo.get('bench-stat')


alpha_style = lambda a, s: dict(alpha=a, linestyle=s)


def fetch_data():
    data = mongo.find_all(projection={
        'result.duration': 1,
        'git.commit': 1,
        'git.tag': 1,
        'timers': 1,
        '_id': 0,
    })

    df = pd.DataFrame(data)
    df['commit'] = df['git.commit'].apply(lambda x: x[0:8])
    df['walltime'] = df['result.duration']
    df['time'] = df['git.tag'].apply(lambda x: int(x.split('-')[1]))
    df['tag'] = df['git.tag'].apply(lambda x: x if len(x) != 7 else x[:5] + '0' + x[5:])
    df['$tag$'] = df['tag'].apply(lambda x: '$%s^{%s}$' % tuple(x.split('-')))

    tagger = defaultdict(int)
    tag_vals = list()
    for v in df['tag']:
        tag_vals.append(tagger[v])
        tagger[v] += 1
    df['no'] = tag_vals

    timers = defaultdict(list)
    for timer_list in df['timers']:
        for timer in timer_list:
            timers[timer['name']].append(timer['duration'])

    for k, v in timers.items():
        df['walltime_'+k] = v

    del df['result.duration'], df['git.commit'], df['git.tag'], df['timers']
    return df


def unwrap(df, vars, prop, y, props):
    result = list()
    for idx, row in df.iterrows():
        for v in vars:
            d = {prop: v, y: row[v]}
            for p in props:
                d[p] = row[p]
            result.append(d)
    return pd.DataFrame(result)