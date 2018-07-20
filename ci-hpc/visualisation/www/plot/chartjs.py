#!/usr/bin/python3
# author: Jan Hybs

import pandas as pd
import numpy as np
from artifacts.db.mongo import Fields as db


def update(d, **kwargs):
    d.update(kwargs)
    return d


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
    def helper_lines(cls, dfs, color='rgba(0,0,0,0.05)', label='!', fill='+1', **kwargs):
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
                fill=fill,
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
    def helper_line(cls, df, color='rgba(0,0,0,0.05)', label='!', **kwargs):
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
                'scaleLabel': {'display': True, 'labelString': 'duration [sec]'},
                #'ticks': {
                #    'beginAtZero': True
                #}
            }]
        },
        'elements': {
            'line': {
                'tension': 0.1,
            }
        },
        'animation': {
            'duration': 500,
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


def _ci_area(df, ci=(+0.05, -0.05), shift=1):
    result = list()
    for c in ci:
        d = df.copy()
        d['y'] = df['y'] + df['y'] * c

        ys = list(d['y'].values)
        if len(ys) > 1:
            ys = [ys[0]] + ys[:-1]

        d['y'] = ys
        d = fillna(d)
        result.append(d)
    return result


def chartjs_category_scatter(df, estimator=np.mean, color='rgba(0, 200, 0, %f)'):
    """
    :type df: pd.DataFrame
    """
    datasets = Datasets()

    # estimator dataset
    result = _group_data(
        df, {
            db.DURATION: estimator,
            db.GIT_COMMIT: 'first',
            db.UUID: 'first',
        }
    )

    std = df.groupby(db.GIT_DATETIME).std()['duration']

    min_df = result.copy()
    min_df['y'] = result['y'] - std
    min_df = fillna(min_df)

    max_df = result.copy()
    max_df['y'] = result['y'] + std
    max_df = fillna(max_df)

    percent_5u, percent_5l, percent_10u, percent_10l = _ci_area(
        result,
        (+0.025, -0.025, +0.05, -0.05)
    )

    p10u, p10l = Dataset.helper_lines([percent_10u, percent_10l], fill='+6')
    p5u, p5l = Dataset.helper_lines([percent_5u, percent_5l], fill='+4')
    pu, pl = Dataset.helper_lines([max_df, min_df], color=color % 0.2, fill='+2')

    datasets.add(
        # *Dataset.helper_lines([percent_10u, percent_10l]),
        # *Dataset.helper_lines([percent_5u, percent_5l]),
        # *Dataset.helper_lines([max_df, min_df], color=color % 0.2),
        # Dataset.helper_lines([max_df, min_df], color=color % 0.2)[0],
        update(p10u, label='+5%'),
        update(p5u, label='+2.5%'),
        update(pu, label='+std'),
        Dataset(
            data=result.to_dict('records'),
            # label='%s [sec]' % 'duration',
            label='%s' % estimator.__name__,
            color=color % 1.0
        ),
        update(pl, label='-std'),
        update(p5l, label='-2.5%'),
        update(p10l, label='-5%'),
    )

    # for g, d in df.groupby('git-datetime'):
    #     values.append(estimator(d['duration']))

    return dict(
        datasets=datasets,
        labels=result['x'].values,
        options=_chart_opts()
    )
