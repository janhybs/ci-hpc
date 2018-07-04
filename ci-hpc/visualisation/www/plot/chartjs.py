#!/usr/bin/python3
# author: Jan Hybs

import pandas as pd
import numpy as np
from artifacts.db.mongo import Fields as db


class Dataset(dict):
    def __init__(self, data, label, color='#0C0', fill=False, spanGaps=True, **kwargs):
        super(Dataset, self).__init__(
            data=data,
            label=label,
            borderColor=color,
            backgroundColor=color,
            fill=fill,
            spanGaps=spanGaps,
        )

        if kwargs:
            self.update(kwargs)

    @classmethod
    def helper_lines(cls, dfs, color='rgba(0,0,0,0.1)', label='!', **kwargs):
        """
        :type dfs: list[pd.DataFrame]
        """
        return [
            Dataset(
                data=dfs[0].to_dict('records'),
                label=label,
                color=color,
                pointRadius=0,
                borderWidth=0.1,
                fill='+1',
                **kwargs
            ),
            Dataset(
                data=dfs[1].to_dict('records'),
                label=label,
                color=color,
                pointRadius=0,
                borderWidth=0.1,
                **kwargs
            ),
        ]

    @classmethod
    def helper_line(cls, df, color='rgba(0,0,0,0.1)', label='!', **kwargs):
        """
        :type df: pd.DataFrame
        """
        return Dataset(
            data=df.to_dict('records'),
            label=label,
            color=color,
            pointRadius=0,
            borderWidth=0.1,
            **kwargs,
        )


class Datasets(list):
    def add(self, *datasets):
        """
        :type datasets: Dataset
        """
        self.extend(datasets)


def _chart_opts(**kwargs):
    return {
        'scales': {
            'yAxes': [{
                'ticks': {
                    'beginAtZero': True
                }
            }]
        },
        'elements': {
            'line': {
                'tension': 0,
            }
        },
        'animation': {
            'duration': 0,
        },
    }


def fillna(df):
    return df.where(pd.notnull(df), None)


def _group_data(df, agg, x=db.GIT_DATETIME, y=db.DURATION, rename=None):
    """
    :type rename: dict
    """
    result = df.groupby('git-datetime').agg(agg).reset_index()

    if not rename:
        rename = dict()

    rename.update(dict(x=x, y=y))
    for k, v in rename.items():
        result[k] = result[v]
        del result[v]
    return result


def chartjs_category_scatter(df, estimator=np.mean):
    """

    :type df: pd.DataFrame
    """

    datasets = Datasets()

    # estimator dataset
    result = _group_data(
        df, {
            db.DURATION: estimator,
            db.GIT_COMMIT: 'first',
        }
    )

    std = _group_data(
        df, {
            db.DURATION: np.std,
            db.GIT_COMMIT: 'first',
        }
    )

    min_df = result.copy()
    min_df['y'] = result['y'] - std['y']
    min_df = fillna(min_df)

    max_df = result.copy()
    max_df['y'] = result['y'] + std['y']
    max_df = fillna(max_df)

    percent_5u = result.copy()
    percent_5u['y'] = result['y'].mean() + result['y'] * 0.025
    percent_5u = fillna(percent_5u)

    percent_5l = result.copy()
    percent_5l['y'] = result['y'].mean() - result['y'] * 0.025
    percent_5l = fillna(percent_5l)

    percent_10u = result.copy()
    percent_10u['y'] = result['y'].mean() + result['y'] * 0.05
    percent_10u = fillna(percent_10u)

    percent_10l = result.copy()
    percent_10l['y'] = result['y'].mean() - result['y'] * 0.05
    percent_10l = fillna(percent_10l)

    datasets.add(
        *Dataset.helper_lines([percent_10u, percent_10l], ),
        *Dataset.helper_lines([percent_5u, percent_5l]),
        *Dataset.helper_lines([max_df, min_df], color='rgba(0,200,0,0.3)'),

        Dataset(
            data=result.to_dict('records'),
            label='%s [%s]' % (estimator.__name__, 'duration'),
        ),
    )

    # for g, d in df.groupby('git-datetime'):
    #     values.append(estimator(d['duration']))

    return dict(
        datasets=datasets,
        labels=result['x'].values,
        options=_chart_opts()
    )
