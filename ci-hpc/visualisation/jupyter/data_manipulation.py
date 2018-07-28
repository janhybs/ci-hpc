#!/bin/python3
# author: Jan Hybs
import collections
import os
from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from artifacts.db import mongo
from utils.config import Config as cfg


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


def normalise_vector(vector, norm='max'):
    if type(vector) is pd.Series:
        return normalize(vector.values.reshape(1, -1), norm).reshape(-1,)
    normalize(vector.reshape(1, -1), norm).reshape(-1,)


def normalise_matrix(matrix, norm='max'):
    normalize(matrix, norm)


def load_data(project, use_cache=True, filename='data.csv', generate=0, filters=dict()):
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
    opts = cfg.get('flow123d.artifactss')
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

                "mesh": "$system.mesh",
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