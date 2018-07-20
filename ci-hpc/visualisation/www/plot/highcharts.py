#!/usr/bin/python3
# author: Jan Hybs


import collections
import copy

import pandas as pd
import numpy as np
import utils.dateutils as dateutils
from artifacts.db.mongo import Fields as db
from visualisation.www.plot.highcharts_config import HighchartsConfig, HighchartsSeries
from visualisation.www.plot.highcharts_config import HighchartsChart as Chart



class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def copy(self):
        """
        :rtype: dotdict
        """
        return self.copy_cls(dotdict)

    def copy_cls(self, cls):
        result = cls()
        for k, v in self.items():
            if isinstance(v, dict):
                result[k] = v.copy()
            else:
                result[k] = copy.copy(v)
        return result


def merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: dict
    """
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]
    return dct


def _fillna(df):
    return df.where(pd.notnull(df), None)


def _group_data(df, agg, x=db.GIT_DATETIME, y=db.DURATION, rename=None):
    """
    :type rename: dict
    """
    result = df.groupby(x).agg(agg).reset_index()

    if rename is False:
        return result

    if rename is None:
        rename = dict(x=x, y=y)

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
        if shift and len(ys) > shift:
            ys = ys[:shift] + ys[:-shift]

        d['y'] = ys
        d = _fillna(d)
        result.append(d)
    return result


def highcharts_frame_in_time(df, estimator=np.mean, title=None, color=None, args=None):
    """
    :type args: argparse.Namespace
    :type df: pd.DataFrame
    """

    x = db.GIT_DATETIME if args.uniform else db.GIT_TIMESTAMP
    linetype = Chart.TYPE_SPLINE if args.smooth else Chart.TYPE_LINE
    areatype = Chart.TYPE_AREA_SPLINE_RANGE if args.smooth else Chart.TYPE_AREA_RANGE

    result = _group_data(
        df, {
            db.DURATION: [estimator, np.std],
            db.GIT_COMMIT: 'first',
            db.UUID: 'first',
        },
        x=x, rename={'x': x}
    )

    commits, uuids = result[db.GIT_COMMIT]['first'], result[db.UUID]['first']
    mean, std = result['duration']['mean'], result['duration']['std']

    stds = pd.DataFrame()
    stds['x'] = result['x']
    stds['low'] = mean - std
    stds['high'] = mean + std

    e5 = pd.DataFrame()
    e5['x'] = result['x']
    e5['low'] = mean - mean*0.025
    e5['high'] = mean + mean*0.025

    e10 = pd.DataFrame()
    e10['x'] = result['x']
    e10['low'] = mean - mean*0.05
    e10['high'] = mean + mean*0.05

    means = pd.DataFrame()
    means['x'] = result['x']
    means['y'] = mean

    # obj.rangeSelector = dotdict(selected=1)
    # obj.showInNavigator = True
    obj = HighchartsConfig()
    obj.title.text = title

    if args.uniform:
        obj.xAxis.categories = result['x'].apply(dateutils.human_format2)
        obj.xAxis.type = Chart.AXIS_TYPE_LINEAR
    else:
        obj.xAxis.type = Chart.AXIS_TYPE_DATETIME

    obj.add(HighchartsSeries(
        type=linetype,
        name='mean',
        data=means,
        commits=commits,
        marker=dotdict(enabled=True),
        uuids=uuids,
        point=dotdict(events=dotdict()),
        color=color,
        allowPointSelect=True,
        zIndex=1,
    ))
    obj.add(HighchartsSeries(
        type=areatype,
        name='std',
        data=stds,
        commits=commits,
        uuids=uuids,
        color='rgba(0, 0, 0, 0.3)',
        fillColor='rgba(0, 0, 0, 0.1)',
        dashStyle='Dash',
    )),
    obj.add(HighchartsSeries(
        type='errorbar',
        name='e5',
        data=e5,
        commits=commits,
        uuids=uuids,
        color='rgba(0, 0, 0, 0.3)',
        # stemColor='#FF0000',
        # whiskerColor='#FF0000',
        lineWidth=0.5,
    ))
    obj.add(HighchartsSeries(
        type='errorbar',
        name='e10',
        data=e10,
        commits=commits,
        uuids=uuids,
        color='rgba(0, 0, 0, 0.3)',
        # stemColor='#FF0000',
        # whiskerColor='#FF0000',
        lineWidth=0.5,
    ))
    return obj


def _rename (df, **kwargs):
    """
    :rtype: pd.DataFrame
    :type df: pd.DataFrame
    """
    for k, v in kwargs.items():
        if v is None:
            del df[k]
        else:
            df[k] = df[v]
            if k != v:
                del df[v]
    return df


def highcharts_frame_bar(df, title=None, color=None):
    """
    :type df: pd.DataFrame
    """
    df = df.sort_values(by='duration', ascending=False)
    df = df[df['duration'] > 0.1]
    df['tag'] = df['tag'].apply(lambda x: '\n'.join(x.split('::')))

    df = _rename(df, name='tag', y='duration', path='path')
    obj = HighchartsConfig()
    obj.tooltip.pointFormat = 'duration <b>{point.y:.2f}</b> sec'
    obj.xAxis.title.text = 'frame'
    obj.yAxis.title.text = 'duration [sec]'
    obj.xAxis.type = 'category'
    obj.legend.align = 'center'
    obj.legend.verticalAlign = 'bottom'
    obj.chart.zoomType = 'x'
    obj.title.text = 'Frame breakdown'

    # obj.xAxis.scrollbar = dotdict(enabled=True)
    # obj.xAxis.min = 0
    # obj.xAxis.max = 4
    # obj.xAxis.tickLength = 0
    # https://jsfiddle.net/gh/get/library/pure/highcharts/highcharts/tree/master/samples/stock/yaxis/inverted-bar-scrollbar

    # del obj.yAxis

    for g, d in df.groupby([db.GIT_DATETIME, db.TEST_SIZE]):
        obj.add(HighchartsSeries(
            type='bar',
            name='%s (%d)' % g,
            data=d.to_dict('records'),
            dataLabels=dotdict(
                enabled=False,
                format='{y:.2f} sec'
            )
        ))
    return obj
