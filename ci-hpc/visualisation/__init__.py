#!/usr/bin/python
# author: Jan Hybs


from utils.logging import logger

import os
import sys
import matplotlib
from utils.config import Config as cfg
from datetime import datetime, timedelta
from sklearn.preprocessing import normalize

matplotlib.use('Agg')

__dir__ = os.path.abspath(os.path.dirname(__file__))
__root__ = os.path.dirname(os.path.dirname(__dir__))
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
from visualisation.utils.plot import tsplot, plot_mean

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
                "_id": 0,
                "uuid": "$problem.uuid",

                'git-branch': '$libs.branch',
                'git-commit': '$libs.commit',
                'git-timestamp': '$libs.timestamp',
                'git-datetime': '$libs.datetime',

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




__all__ = [
    'np', 'pd', 'sns', 'plt', 'sc', 'w', 'logger', 'mongo', 'normalise_vector', 'normalise_matrix',
    'tsplot', 'plot_mean',
    'dateutils', 'datautils',
    'load_data',
]
