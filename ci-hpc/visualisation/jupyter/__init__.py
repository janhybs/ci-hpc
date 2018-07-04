#!/usr/bin/python
# author: Jan Hybs


from utils.logging import logger

import os
import sys
import matplotlib
matplotlib.use('Agg')

from utils.config import Config as cfg
from datetime import datetime, timedelta
from sklearn.preprocessing import normalize


__dir__ = os.path.abspath(os.path.dirname(__file__))
__root__ = os.path.dirname(os.path.dirname(os.path.dirname(__dir__)))
__cfg__ = os.path.join(__root__, 'cfg')
secret_path = os.path.join(__cfg__, 'secret.yaml')

import numpy as np
import scipy as sc
import pandas as pd
import seaborn as sns
import ipywidgets as w
import utils.dates as dateutils
import utils.data as datautils


from matplotlib import pyplot as plt
from artifacts.db import mongo
from visualisation.utils.plot import tsplot, plot_mean, plot_mean_with_area

cfg.init(secret_path)


def normalise_vector(vector, norm='max'):
    if type(vector) is pd.Series:
        return normalize(vector.values.reshape(1, -1), norm).reshape(-1,)
    normalize(vector.reshape(1, -1), norm).reshape(-1,)


def normalise_matrix(matrix, norm='max'):
    normalize(matrix, norm)


def load_data(use_cache=True, filename='data.csv', generate=0, filters=dict()):
    """
    :rtype: pandas.core.frame.DataFrame
    """

    def generate_samples(data):
        data_copy = data.copy()
        items = list()
        for g, d in data_copy.groupby(['test-name', 'case-name']):
            shift = False
            for i in range(generate):
                if np.random.rand() > 0.95:
                    shift = True
                item_copy = d.iloc[0].copy()
                duration = item_copy['duration']
                delta = duration * (np.random.randn() / 25) + (duration * 0.2 if shift else 0)
                item_copy['duration'] = duration + delta + float(i) / generate / 100
                item_copy['git-datetime'] = item_copy['git-datetime'] + timedelta(days=int(i / 5) / 5)
                items.append(item_copy)
        return items

    if use_cache and os.path.exists(filename):
        data = pd.read_csv(filename)
        data['git-datetime'] = pd.to_datetime(data['git-datetime'])
        if generate:
            items = generate_samples(data)
            if items:
                data = data.append(items, ignore_index=True)
        return data

    m = mongo.Mongo()
    opts = cfg.get('flow123d.artifacts')
    db = m.client.get_database(opts['dbname'])
    files_col = db.get_collection(opts['files_col'])
    reports_col = db.get_collection(opts['reports_col'])
    iterable = reports_col.aggregate([
        {
            '$match': filters
        },
        {
            "$unwind": "$libs"
        },
        {
            "$project": {
                "_id": 1,
                "uuid": "$problem.uuid",

                'git-branch': '$libs.branch',
                'git-commit': '$libs.commit',
                'git-timestamp': '$libs.timestamp',
                'git-datetime': '$libs.datetime',
                'returncode': '$problem.returncode',

                "test-name": "$problem.test-name",
                "case-name": "$problem.case-name",
                "cpu": "$problem.cpu",
                "nodename": "$problem.nodename",
                "test-size": "$problem.task-size",
                "machine": "$system.machine",
                'frame': '$timer.tag',
                'duration': '$timer.cumul-time-max',
            }
        },
    ])
    items = list(iterable)
    data = pd.DataFrame(items)
    data.to_csv(filename, index=False)

    if generate:
        items = generate_samples(data)
        if items:
            data = data.append(items, ignore_index=True)
    return data


def add_metrics(data):
    data['commit-date'] = data['git-datetime'].apply(dateutils.long_format)
    for g, d in data.groupby(['test-name', 'case-name']):
        data.loc[d.index, 'duration-relative'] = normalise_vector(d['duration'], norm='max').T
        # data.loc[d.index, 'duration-relative'] = d['duration']/d['duration'].max()

        first_commit = sorted(list(set(d['git-datetime'])))[0]
        max_first_commit = d[d['git-datetime'] == first_commit]['duration'].max()
        data.loc[d.index, 'duration-relative-start'] = d['duration'] / max_first_commit
    return data


def dual_plot(conditions, *args, plot_func, error_kwargs, **kwargs):
    ok_args = [a[conditions == 0] for a in args]
    er_args = [a[conditions == 1] for a in args]
    plot_func(*ok_args, **kwargs)
    for k, v in error_kwargs.items():
        kwargs[k] = v
    plot_func(*er_args, **kwargs)


def facetgrid_opts(data, x, y, z, x_space=15, aspect=2, sharex=False, sharey=False):
    # g = sns.FacetGrid(subdata, row='case-name', sharey=False, sharex=sharex, size=3, aspect=2, hue='case-name')
    # g = sns.FacetGrid(subdata, col='case-name', col_wrap=2, sharey=False, sharex=sharex, size=3, aspect=2, hue='case-name')

    x_series, y_series = data[x], data[y]
    col_wrap = 1 + int(np.floor(x_space / len(datautils.olist(x_series))))
    inches = 8

    if col_wrap == 1:
        return dict(
            row=y_series.name,
            size=inches/aspect,
            aspect=aspect,
            hue=y_series.name,
            sharey=sharey or False,
            sharex=sharex or (True if z.find('relative') != -1 else False)
        )
    else:
        return dict(
            col=y_series.name,
            col_wrap=col_wrap,
            aspect=aspect,
            size=int((inches-col_wrap+0.0)/aspect),
            hue=y_series.name,
            sharey=sharey or False,
            sharex=sharex or (True if z.find('relative') != -1 else False)
        )



__all__ = [
    'np', 'pd', 'sns', 'plt', 'sc', 'w', 'logger', 'mongo', 'normalise_vector', 'normalise_matrix',
    'tsplot', 'plot_mean', 'plot_mean_with_area', 'dual_plot',
    'dateutils', 'datautils',
    'load_data', 'add_metrics', 'facetgrid_opts',
]
