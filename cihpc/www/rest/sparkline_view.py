#!/bin/python3
# author: Jan Hybs

import argparse
import base64
import datetime
import itertools
import json
import logging
from collections import namedtuple

import numpy as np
import pandas as pd

from cihpc.common.utils import datautils as du, dateutils, strings
from cihpc.common.utils.caching import cached
from cihpc.common.utils.strings import str2bool
from cihpc.common.utils.timer import Timer
from cihpc.core.db import CIHPCMongo
from cihpc.www.cfg.project_config import ProjectConfig, ViewMode
from cihpc.www.engines.highcharts import ChartGroup
from cihpc.www.rest import ConfigurableView


logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--failed', type=str2bool, default=False)
parser.add_argument('--uniform', type=str2bool, default=True)
parser.add_argument('--smooth', type=str2bool, default=True)
parser.add_argument('--show-errorbar', type=str2bool, default=True)
parser.add_argument('--show-boxplot', type=str2bool, default=True)
parser.add_argument('--scaling', choices=['none', 'weak', 'strong'], default='none')
parser.add_argument('-f', '--ff', action='append', default=[], dest='filters')
parser.add_argument('-g', '--gg', action='append', default=[], dest='groups')


class SparklineView(ConfigurableView):
    """
    a view which returns a list of chart configuration with data when called
    if no data matches the query, dict is returned with keys 'error' and 'description'
    """

    def __init__(self):
        super(SparklineView, self).__init__()

    @staticmethod
    def prepare(project, base64data=None):
        if base64data:
            options = json.loads(
                base64.decodebytes(base64data.encode()).decode()
            )
        else:
            logger.warning('no options given')
            options = dict()

        logger.info(strings.to_json(options))

        config = ProjectConfig.get(project)
        mongo = CIHPCMongo.get(project)

        return namedtuple('ViewInit', ['options', 'config', 'mongo'])(options, config, mongo)

    @Timer.decorate('Sparkline: get', logger.info)
    def get(self, project, base64data=''):
        return sparkline_view(project, base64data)


# cache the charts
@cached()
def sparkline_view(project, base64data=''):
    options, config, mongo = SparklineView.prepare(project, base64data)

    mode = ViewMode(options.get('mode', {}).get('mode', ViewMode.TIME_SERIES.value))
    squeeze = int(options.get('squeeze', {}).get('value', 1))
    interval = options.get('range', {})

    field_set = config.fields.required_fields()
    filter_dict = options['filters']

    if interval and 'from' in interval and 'to' in interval:
        filter_dict[config.fields.git.datetime.name] = {
            '$gte': datetime.datetime.fromtimestamp(int(interval['from'])),
            '$lte': datetime.datetime.fromtimestamp(int(interval['to'])),
        }

    projection_list = set(filter_dict.keys()) | field_set
    db_find_fields = dict(zip(projection_list, itertools.repeat(1)))

    db_find_filters = du.filter_keys(
        filter_dict,
        forbidden=("", None, "*")
    )

    with Timer('db find & apply', log=logger.debug):
        data_frame = pd.DataFrame(
            mongo.find_all(
                db_find_filters,
                db_find_fields,
            )
        )

        if data_frame.empty:
            return SparklineView.error_empty_df(db_find_filters)

        sort_field = config.fields.git.datetime.name
        data_frame = data_frame.sort_values(by=sort_field, ascending=False).reset_index(drop=True)

        config.fields.apply_to_df(data_frame)
        data_frame[':merged:'] = 'g(?)'

    if mode is ViewMode.SCALE_VIEW:
        # split charts based on commit when in scale-view mode
        # if config.fields.git.datetime:
        #     config.test_view.groupby['git.datetime'] = 'date'
        # else:
        config.test_view.groupby['git.commit'] = 'commit'

        config.test_view.groupby = du.filter_values(
            config.test_view.groupby,
            forbidden=(config.fields.problem.size.name, config.fields.problem.cpu.name)
        )
        chart_options = du.dotdict(
            y=config.fields.result.duration.name,
            x=config.fields.problem.cpu.name,
            c=config.fields.git.commit.name,
            groupby={k: v for k, v in config.test_view.groupby.items() if options['groupby'].get(k, False)},
            colorby={k: v for k, v in config.test_view.groupby.items() if
                     not options['groupby'].get(k, False)},
        )
        data_frame[chart_options.x] = data_frame[chart_options.x].apply(str)

    elif mode is ViewMode.TIME_SERIES:

        if config.fields.problem.cpu:
            config.test_view.groupby[config.fields.problem.cpu.name] = 'cpu'

        if config.fields.problem.size:
            config.test_view.groupby[config.fields.problem.size.name] = 'size'

        if config.fields.problem.test:
            config.test_view.groupby[config.fields.problem.test.name] = 'test'

        if config.fields.problem.case:
            config.test_view.groupby[config.fields.problem.case.name] = 'case'

        # if self.config.fields.problem.test and self.options['groupby'].get(self.config.fields.problem.test.name, False):
        #     self.config.test_view.groupby[self.config.fields.problem.test.name] = 'test'
        #     self.options['groupby'][self.config.fields.problem.test.name] = True
        #
        # if self.config.fields.problem.case and self.options['groupby'].get(self.config.fields.problem.case.name, False):
        #     self.config.test_view.groupby[self.config.fields.problem.case.name] = 'size'
        #     self.options['groupby'][self.config.fields.problem.case.name] = True

        chart_options = du.dotdict(
            y=config.fields.result.duration.name,
            x=config.fields.git.datetime.name,
            c=config.fields.git.commit.name,
            groupby={k: v for k, v in config.test_view.groupby.items() if
                     options['groupby'].get(k, False) is True},
            colorby={k: v for k, v in config.test_view.groupby.items() if
                     options['groupby'].get(k, False) is False},
        )
        print(chart_options)
    else:
        raise Exception('Given mode is not supported %s' % mode)

    chart_group = ChartGroup(chart_options, options)
    if not chart_group:
        return SparklineView.show_error(
            status=300,
            message='No chart series selected',
            description='<p>All of the chart series are disabled, so no chart can be displayed. '
                        'Please enable at least one of the chart type series</p>'
                        '<a class="btn btn-warning" data-toggle="modal" data-target="#modal-options">Click here to open configuration.</a>'
        )

    charts = list()
    for group_values, group_keys, group_names, group_data in SparklineView.group_by(data_frame, chart_options.groupby):
        group_title = du.join_lists(group_names, group_values, '<dt>{}</dt><dd>{}</dd>', '')
        group_title = '<dl>%s</dl>' % group_title

        series = list()
        extra = dict(size=list())
        colors_iter = iter(config.color_palette.copy() * 5)
        for color_values, color_keys, color_names, color_data in SparklineView.group_by(group_data,
                                                                                        chart_options.colorby):
            color_title = du.join_lists(color_names, color_values, '<small>{}</small> <b>{}</b>', ', ')
            if color_title == ' = ':
                color_title = '*'
            color = next(colors_iter)

            if squeeze and squeeze > 1:
                merge_unique = sorted(list(set(color_data[chart_options.x])))
                merge_groups = np.repeat(np.arange(int(len(merge_unique) / squeeze + 1)), squeeze)
                merge_unique_len = len(merge_unique)
                merge_map = dict()
                for i in range(merge_unique_len):
                    s = merge_groups[i]
                    bb, ee = s * squeeze + 1, min((s + 1) * squeeze, merge_unique_len)
                    b, e = merge_unique[bb - 1], merge_unique[ee - 1]
                    cnt = ee - (bb - 1)
                    if b == e:
                        merge_map[merge_unique[i]] = 'group %s (1 item, %s)' % (chr(65 + s), b)
                    else:
                        if isinstance(b, datetime.datetime):
                            duration = dateutils.human_interval(b, e)
                            merge_map[merge_unique[i]] = 'group %s (%d items, period of %s)' % (
                                chr(65 + s), cnt, duration)
                        else:
                            merge_map[merge_unique[i]] = 'group %s (%d items, %s - %s)' % (chr(65 + s), cnt, b, e)

                # color_data[':merged:'] = color_data[chart_options.x].map(merge_map)
                # TODO carefully think this through
                color_data[chart_options.x] = color_data[chart_options.x].map(merge_map)
                # chart_options.x = ':merged:'

            with Timer('agg ' + color_title, log=logger.info):
                cd_group = color_data.groupby(chart_options.x, sort=True).aggregate({
                    chart_options.c: lambda x: list(set(x)),
                    chart_options.y: chart_group.y_metrics.items(),
                    '_id'          : lambda x: list(set(x)),
                })

            if chart_group.boxplot_chart:
                series.append(chart_group.boxplot_chart.get_chart(
                    cd_group, color_title,
                    color=color(0.8)
                ))

            if chart_group.std_chart:
                series.append(chart_group.std_chart.get_chart(
                    cd_group, color_title,
                    color=color(0.3),
                    fillColor=color(0.1)
                ))

            if chart_group.ci_chart:
                series.append(chart_group.ci_chart.get_chart(
                    cd_group, color_title,
                    color=color(0.3),
                    fillColor=color(0.1)
                ))

            if chart_group.errorbar_chart:
                series.append(chart_group.errorbar_chart.get_chart(
                    cd_group, color_title,
                    color=color(0.3),
                    fillColor=color(0.1)
                ))

            if chart_group.mean_chart:
                series.append(chart_group.mean_chart.get_chart(
                    cd_group, color_title,
                    color=color(1.0),
                ))

            if chart_group.median_chart:
                series.append(chart_group.median_chart.get_chart(
                    cd_group, color_title,
                    color=color(1.0),
                ))

            if series:
                series[-1]['extra'] = {
                    '_id'    : cd_group['_id'],
                    'commits': cd_group[chart_options.c],
                }

            extra['size'].append(len(cd_group))

        charts.append(dict(
            title=group_title,
            series=series,
            xAxis=dict(title=dict(text=chart_options.x)),
            yAxis=dict(title=dict(text=chart_options.y)),
            extra=extra,
        ))

    return dict(
        status=200,
        data=charts
    )
