#!/usr/bin/python3
# author: Jan Hybs


import collections
import copy

import pandas as pd
import numpy as np
import utils.dateutils as dateutils
from artifacts.db.mongo import Fields as db
from utils.datautils import ensure_iterable
from utils.logging import logger
from utils.timer import Timer
from visualisation.www.plot.highcharts_config import HighchartsConfig, HighchartsSeries
from visualisation.www.plot.highcharts_config import HighchartsChart as Chart


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


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
    return df.where(pd.notnull(df), None).round(2)


def _group_data(df, agg, x=db.GIT_DATETIME, y=db.DURATION, rename=None):
    """
    :type rename: dict
    """
    with Timer('highcharts: data group: agg', log=logger.debug):
        result = df.groupby(x).aggregate(agg).reset_index()

    if rename is False:
        return result

    if rename is None:
        rename = dict(x=x, y=y)

    dels = set()
    for k, v in rename.items():
        result[v] = result[k]
        dels.add(k)

    for k in dels:
        del result[k]
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


def highcharts_frame_in_time(df, config, estimator=np.mean, title=None, color=None, args=None, add_std=True, add_errorbar=True, metric_name=None):
    """
    :type config: visualisation.www.plot.cfg.project_config.ProjectConfig
    :type args: argparse.Namespace
    :type df: pd.DataFrame
    """

    x = config.test_view.x_prop
    y = config.test_view.y_prop
    linetype = Chart.TYPE_SPLINE if config.test_view.smooth else Chart.TYPE_LINE
    areatype = Chart.TYPE_AREA_SPLINE_RANGE if config.test_view.smooth else Chart.TYPE_AREA_RANGE

    agg, renames = config.get_test_view_groupby()

    agg.update({
        y: [estimator, np.std],
    })
    renames.update({
        x: 'x'
    })

    with Timer('highcharts: data group', log=logger.debug):
        result = _group_data(
            df, agg, x=x, rename=renames
        )

    commits, uuids = result['commit'], result['id']
    mean, std = result[y]['mean'], result[y]['std']

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
    obj.xAxis.title.text = config.test_view.x_prop
    obj.yAxis.title.text = config.test_view.y_prop

    obj.xAxis.type = 'category'

    obj.add(HighchartsSeries(
        type=linetype,
        name='mean' if not metric_name else metric_name,
        data=_fillna(means),
        commits=commits,
        marker=dotdict(enabled=True),
        uuids=uuids,
        point=dotdict(events=dotdict()),
        color=color,
        allowPointSelect=True,
        zIndex=1,
    ))

    if add_std:
        obj.add(HighchartsSeries(
            type=areatype,
            name='std',
            data=_fillna(stds),
            commits=commits,
            uuids=uuids,
            color='rgba(0, 0, 0, 0.2)',
            fillColor='rgba(0, 0, 0, 0.05)',
            dashStyle='Dash',
        )),

    if add_errorbar:
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


def highcharts_sparkline_in_time(df, config, estimator=np.mean, title=None, color=None, args=None, add_std=True, add_errorbar=True, metric_name=None):
    """
    :type config: visualisation.www.plot.cfg.project_config.ProjectConfig
    :type args: argparse.Namespace
    :type df: pd.DataFrame
    """

    x = config.test_view.x_prop
    y = config.test_view.y_prop
    linetype = Chart.TYPE_SPLINE if config.test_view.smooth else Chart.TYPE_LINE
    areatype = Chart.TYPE_AREA_SPLINE_RANGE if config.test_view.smooth else Chart.TYPE_AREA_RANGE

    agg, renames = config.get_test_view_groupby()

    agg.update({
        y: [estimator, np.std],
    })
    renames.update({
        x: 'x'
    })

    with Timer('highcharts: data group', log=logger.debug):
        result = _group_data(
            df, agg, x=x, rename=renames
        )

    commits, uuids = result['commit'], result['id']
    mean, std = result[y]['mean'], result[y]['std']

    means = pd.DataFrame()
    means['x'] = result['x']
    means['y'] = mean

    obj = HighchartsConfig()
    # obj.rangeSelector = dotdict(selected=1)
    # obj.showInNavigator = True
    obj.title.text = title
    obj.xAxis.title.text = config.test_view.x_prop
    obj.yAxis.title.text = config.test_view.y_prop

    obj.xAxis.type = 'category'

    obj.add(HighchartsSeries(
        type=linetype,
        name='mean' if not metric_name else metric_name,
        data=_fillna(means),
        commits=commits,
        marker=dotdict(enabled=True),
        uuids=uuids,
        point=dotdict(events=dotdict()),
        color=color(1.0),
        allowPointSelect=True,
        zIndex=1,
    ))

    if add_std:
        info = df.groupby(x)[y].describe()
        info = info.reset_index()
        info = _rename(info, **{'x': x})
        info = info[['x', 'min', '25%', '50%', '75%', 'max']]

        obj.add(HighchartsSeries(
            type='boxplot',
            name='info',
            data=_fillna(info),
            commits=commits,
            uuids=uuids,
            color=color(1.0),
        ))
        # stds = pd.DataFrame()
        # stds['x'] = result['x']
        # stds['low'] = mean - std
        # stds['high'] = mean + std
        # ,HighchartsSeries(
        #     type=areatype,
        #     name='std',
        #     data=_fillna(stds),
        #     commits=commits,
        #     uuids=uuids,
        #     color=color(0.2),
        #     fillColor=color(0.2),
        #     dashStyle='Dash',
        # )),
    if add_errorbar:
        e5 = pd.DataFrame()
        e5['x'] = result['x']
        e5['low'] = mean - mean * 0.025
        e5['high'] = mean + mean * 0.025

        obj.add(HighchartsSeries(
            type='arearange',
            # type='areasplinerange',
            name='e5',
            data=e5,
            commits=commits,
            uuids=uuids,
            color=color(0.05),
            # stemColor='#FF0000',
            # whiskerColor='#FF0000',
            lineWidth=0.5,
        ))

    return obj


def _rename(df, **kwargs):
    """
    :rtype: pd.DataFrame
    :type df: pd.DataFrame
    """
    dels = set()
    for new, old in kwargs.items():
        if old is None:
            dels.add(new)
        else:
            df[new] = df[old]
            if new != old:
                dels.add(old)
    for d in dels:
        del df[d]
    return df


def highcharts_frame_bar(df, config):
    """
    :type df: pd.DataFrame
    :type config: visualisation.www.plot.cfg.project_config.ProjectConfig
    """
    x = config.frame_view.x_prop
    y = config.frame_view.y_prop

    df = df.sort_values(by=y, ascending=False)
    df = df[df[y] > 0.1]
    # df[args.rename['name']] = df[args.rename['name']].apply(lambda x: '\n'.join(x.split('::')))
    rename = {
        'y': y,
        'name': x,
        'path': x,
    }
    rename.update(config.frame_view.groupby)

    df = _rename(df, **rename)
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

    names = list(config.frame_view.groupby.keys())

    for groupby_name, groupby_data in df.groupby(names):
        title_dict = dict(zip(names, ensure_iterable(groupby_name)))

        obj.add(HighchartsSeries(
            type='bar',
            name=', '.join('%s=<b>%s</b>' % (str(k), str(v)) for k, v in title_dict.items()),
            data=groupby_data.to_dict('records'),
            dataLabels=dotdict(
                enabled=False,
                format='{y:.2f} sec'
            )
        ))
    return obj
