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

# plt.style.use("dark_background")
# sea.set_style("whitegrid")
#sea.set_style("darkgrid", {"axes.facecolor": ".9"})
#sea.set()
sea.set_style('whitegrid', {'grid.color': '0.9'})
sea.set_palette('bright')
sea.axes_style()
np.random.seed(1234)
# from IPython.core.display import display, HTML
# display(HTML("<style>.container { width: 75% !important; } .rendered_htmlm {max-width: 850px;}</style>"))


global_configuration.cfg_secret_path = '/home/jan-hybs/projects/ci-hpc/cfg/secret.yaml'
mongo = CIHPCMongo.get('bench-stat')


alpha_style = lambda a, s: dict(alpha=a, linestyle=s)
qs = dict(
    q1=list(range(0, 6)),
    q2=list(range(6, 12)),
    q3=list(range(12, 18)),
    q4=list(range(18, 24)),
)

qs_step = 6
qs = {'q%d'%(i+1): list(range(i*qs_step, (i+1)*qs_step)) for i, x in enumerate(range(0, 24, qs_step))}


def figsave(name:str = None, fmt='pdf', i=1, **kwargs):
    if not name:
        try:
            name = plt.gcf()._suptitle.get_text()
        except:
            name = plt.gca().get_title()

    n = '%03d-%s.%s' % (i, name.lower().replace(' ', '-'), fmt)
    plt.savefig(n, **kwargs)
    return


def smart_date(timestamp):
    ymd = '{timestamp.year}-{timestamp.month:02d}-{timestamp.day:02d}'.format(timestamp=timestamp)
    hour = timestamp.hour
    for k, items in qs.items():
        if hour in items:
            ymd = '%s-%s(%02d-%02d)h' % (ymd, k, min(items), max(items))
            break
    return ymd


def cluster_1d(data, spacing, value_fmt='%d'):
    group_id = -1
    prev_timestamp = 0
    groups = list()
    
    for d in data:       
        if (d - prev_timestamp) > spacing:
            prev_timestamp = d
            group_id += 1
        groups.append(value_fmt % group_id if value_fmt else group_id)
    return groups


def fetch_data(group_interval=60*60*1):
    data = mongo.find_all(projection={
        'result.duration': 1,
        'git.commit': 1,
        'git.tag': 1,
        'timers': 1,
        'system.hostname': 1,
    })
   
    df = pd.DataFrame(data)
    df['commit'] = df['git.commit'].apply(lambda x: x[0:8])
    df['walltime'] = df['result.duration']
    df['timepoint'] = df['git.tag'].apply(lambda x: int(x.split('-')[1]))
    df['tag'] = df['git.tag'].apply(lambda x: x if len(x) != 7 else x[:5] + '0' + x[5:])
    df['$tag$'] = df['tag'].apply(lambda x: '$%s^{%s}$' % tuple(x.split('-')))
    df['hpc'] = df['system.hostname'].apply(lambda x: x.split('.')[0])
    df['excl'] = df['hpc'] == 'charon20'
    df['datetime'] = df['_id'].apply(lambda x: x.generation_time)
    df['timestamp'] = df['datetime'].apply(lambda x: x.timestamp())
    df = df.sort_values(by='timestamp').reset_index(drop=True)
    
    excl = df['excl'] == True
    nonexcl = df['excl'] == False
    
    df.loc[nonexcl, 'dt_group'] = cluster_1d(
        df[nonexcl]['timestamp'],
        group_interval,
        'n%d'
    )
    df.loc[excl, 'dt_group'] = cluster_1d(
        df[excl]['timestamp'],
        group_interval*24,
        'e%d'
    )
    
    dt_map = dict()
    for i in set(df['dt_group']):
        d = df[df['dt_group'] == i]['datetime']
        if d.empty:
            continue
        dt_map[i] = '%s (%s - %s)' % (
            d.min().strftime("%Y-%m-%d"),
            d.min().strftime("%H:%M"),
            d.max().strftime("%H:%M"),
        )
    df['dt'] = df['dt_group'].map(dt_map)

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

    del df['result.duration'], df['git.commit'], df['git.tag'], df['timers'], df['system.hostname']
    return df.sort_values(by='tag').reset_index(drop=True)


def unwrap(df, vars, prop, y, props):
    result = list()
    for idx, row in df.iterrows():
        for v in vars:
            d = {prop: v, y: row[v]}
            for p in props:
                d[p] = row[p]
            result.append(d)
    return pd.DataFrame(result)


def map_facetgrid(g, func, *props):
    callbacks = defaultdict(list)

    for (row_i, col_j, hue_k), data_ijk in g.facet_data():
        if not data_ijk.values.size:
            continue
        callbacks[(row_i, col_j)].append([data_ijk[v] for v in props])

    for (row_i, col_j), series in callbacks.items():
        plt.sca(g.facet_axis(row_i, col_j))
        func(*series)


def sample(df, per_group=1, *groups):
    if not groups:
        return df.sample(n=per_group)

    group_data = list()
    for g, d in df.groupby(by=list(groups)):
        group_data.append(d.sample(per_group))
    return pd.concat(group_data)