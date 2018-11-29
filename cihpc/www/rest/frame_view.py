#!/bin/python3
# author: Jan Hybs

import argparse
import base64
import itertools
import json
import logging

import numpy as np
import pandas as pd
from bson import objectid

from cihpc.common.utils import datautils as du, strings
from cihpc.common.utils.caching import cached
from cihpc.common.utils.timer import Timer
from cihpc.core.db import CIHPCMongo
from cihpc.www.cfg.project_config import ProjectConfig
from cihpc.www.rest import ConfigurableView


logger = logging.getLogger(__name__)


def str2bool(v):
    if v.lower() in ('yes', 'true', '1'):
        return True
    elif v.lower() in ('no', 'false', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


parser = argparse.ArgumentParser()
parser.add_argument('--failed', type=str2bool, default=False)
parser.add_argument('--uniform', type=str2bool, default=True)
parser.add_argument('--smooth', type=str2bool, default=True)
parser.add_argument('--show-errorbar', type=str2bool, default=True)
parser.add_argument('--show-boxplot', type=str2bool, default=True)
parser.add_argument('--scaling', choices=['none', 'weak', 'strong'], default='none')
parser.add_argument('-f', '--ff', action='append', default=[], dest='filters')
parser.add_argument('-g', '--gg', action='append', default=[], dest='groups')


class FrameView(ConfigurableView):
    """
    a view which returns a list of chart configuration with data when called
    if no data matches the query, dict is returned with keys 'error' and 'description'
    """

    @Timer.decorate('Frameview: get', logger.info)
    def get(self, project, base64data=''):
        return frame_view(project, base64data)


# cache the charts
@cached()
def frame_view(project, base64data=''):
    if base64data:
        options = json.loads(
            base64.decodebytes(base64data.encode()).decode()
        )
    else:
        options = dict()

    print(
        strings.to_json(options)
    )

    config = ProjectConfig.get(project)
    _ids = [objectid.ObjectId(x) for y in options['_ids'] for x in y]

    field_set = config.fields.required_fields()
    filter_dict = options['filters']

    projection_list = set(filter_dict.keys()) | field_set
    projection_list.add(config.frame_view.unwind)
    db_find_fields = dict(zip(projection_list, itertools.repeat(1)))

    # add _ids to selector
    db_find_filters = du.filter_keys(
        filter_dict,
        forbidden=("", None, "*")
    )
    db_find_filters['_id'] = {'$in': _ids}

    with Timer('db find & apply', log=logger.debug):
        mongo = CIHPCMongo.get(project)
        data_frame = pd.DataFrame(
            mongo.aggregate(
                match=db_find_filters,
                project=db_find_fields,
                unwind='$%s' % config.frame_view.unwind
            )
        )

        if data_frame.empty:
            return FrameView.error_empty_df(db_find_filters)

        config.fields.apply_to_df(data_frame)

    chart_options = du.dotdict(
        y=config.frame_view.fields.timers.duration.name,
        x=config.frame_view.fields.timers.name.name,
        n=config.frame_view.fields.timers.path.name,
        groupby={},
        colorby=config.frame_view.groupby,
    )
    if not config.frame_view.fields.timers.path:
        data_frame[config.frame_view.fields.timers.path.name] = config.frame_view.fields.timers.name.name

    print(chart_options)

    charts = list()
    for group_values, group_keys, group_names, group_data in FrameView.group_by(data_frame, chart_options.groupby):
        group_title = du.join_lists(group_names, group_values, '{} = <b>{}</b>', '<br />')
        group_title = du.join_lists(group_names, group_values, '{} = <b>{}</b>', '<br />')

        series = list()
        colors_iter = iter(config.color_palette.copy() * 5)
        for color_values, color_keys, color_names, color_data in FrameView.group_by(group_data, chart_options.colorby):
            color_title = du.join_lists(color_names, color_values, '{} = {}', ', ')
            color = next(colors_iter)

            print(color_title)

            with Timer('agg ' + color_title, log=logger.info):
                # color_data = color_data.groupby(chart_options.x).agg({
                #     chart_options.y: 'mean',
                #     chart_options.n: 'first'
                # }).sort_values(by=chart_options.y, ascending=False).head(50)

                small_values = color_data[color_data[chart_options.y] < 0.5]
                color_data = color_data[color_data[chart_options.y] >= 0.5]

                small_values_grouped = small_values.groupby(chart_options.x).agg({
                    chart_options.y: 'mean',
                }).sum()

                color_data = color_data.append({
                    chart_options.y: small_values_grouped[chart_options.y],
                    chart_options.x: 'values &lt; 0.5',
                    chart_options.n: 'sum of the means of the values lesser than 0.5 sec',

                }, ignore_index=True)

                color_data_grouped = color_data.groupby(chart_options.x).agg({
                    chart_options.y: {
                        '25%': lambda x: np.percentile(x, 25),
                        '75%': lambda x: np.percentile(x, 75),
                    },
                    chart_options.n: 'first',
                }).reset_index()

                print(color_data_grouped)

                columnrange = pd.DataFrame()
                columnrange['y'] = list(color_data_grouped[chart_options.x])
                columnrange['n'] = list(color_data_grouped[chart_options.n]['first'])
                columnrange['low'] = list(color_data_grouped[chart_options.y]['25%'])
                columnrange['high'] = list(color_data_grouped[chart_options.y]['75%'])
                columnrange = columnrange.sort_values(by='high', ascending=False).reset_index(drop=True)

                a, b = list(columnrange['y']), list(columnrange['n'])
                columnrange.drop(columns=['n'], inplace=True)

                series.append(dict(
                    type='columnrange',
                    extra={
                        'path': dict(zip(a, b))
                    },
                    data=du.dropzero(du.fillna(columnrange.round(3))),
                    name='Q1-Q3 (%s)' % color_title,
                    color=color(0.7)),
                )

                color_data = color_data.reset_index()
                scatter = pd.DataFrame()
                scatter['y'] = list(color_data[chart_options.x])
                scatter['x'] = list(color_data[chart_options.y])
                scatter['n'] = list(color_data[chart_options.n])
                scatter = scatter.sort_values(by='x', ascending=False).reset_index(drop=True)

                a, b = list(scatter['y']), list(scatter['n'])

                paths = list(scatter['n'])
                scatter.drop(columns=['n'], inplace=True)

                series.append(dict(
                    type='scatter',
                    extra={
                        'path': dict(zip(a, b)),
                    },
                    data=du.dropzero(du.fillna(scatter.round(3))),
                    name='mean (%s)' % color_title,
                    color=color(0.7)),
                )

        charts.append(dict(
            title=group_title,
            xAxis=dict(title=dict(text=None)),
            yAxis=dict(title=dict(text=None)),
            series=series,
        ))

    return dict(
        status=200,
        data=charts
    )
