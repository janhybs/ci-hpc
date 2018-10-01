#!/bin/python3
# author: Jan Hybs

import argparse
import base64
import datetime

import itertools
import json

from flask_restful import Resource
from artifacts.db.mongo import CIHPCMongo

import pandas as pd
import numpy as np

from utils import strings, dateutils
from utils import datautils as du
from utils.logging import logger
from utils.strings import str2bool
from utils.timer import Timer
from visualisation.www.plot.cfg.project_config import ProjectConfig, ViewMode


parser = argparse.ArgumentParser()
parser.add_argument('--failed', type=str2bool, default=False)
parser.add_argument('--uniform', type=str2bool, default=True)
parser.add_argument('--smooth', type=str2bool, default=True)
parser.add_argument('--show-errorbar', type=str2bool, default=True)
parser.add_argument('--show-boxplot', type=str2bool, default=True)
parser.add_argument('--scaling', choices=['none', 'weak', 'strong'], default='none')
parser.add_argument('-f', '--ff', action='append', default=[], dest='filters')
parser.add_argument('-g', '--gg', action='append', default=[], dest='groups')


class AChart(object):
    _metrics = list()
    _chart_type = None
    _chart_name = None

    def __init__(self, opts, enabled=False):
        self.opts = opts
        self.enabled = enabled

        self.chart_type = self._chart_type
        self.chart_name = self._chart_name
        self.metrics = self._metrics

    def get_metrics(self):
        if self.enabled:
            return {k: True for k in self.metrics}
        return {}

    @staticmethod
    def __round_and_fill(df):
        return du.fillna(df.round(2))

    def get_chart_data(self, df):
        return self.__round_and_fill(
            self._compute(df)
        )

    def get_chart(self, df, title=None, **kwargs):
        result = dict(
            type=self.chart_type,
            data=self.get_chart_data(df),
            name=self.chart_name + (' (%s)' % title if title not in ('*', '', None) else ''),
        )
        result.update(kwargs)
        return result

    def _compute(self, df):
        raise Exception("Not supported")

    def __bool__(self):
        return self.enabled


class ChartErrorBar(AChart):
    _metrics = ['mean']
    _chart_type = 'errorbar'
    _chart_name = 'mean +- {}%'

    def __init__(self, opts, enabled=False, interval=0.025):
        super(ChartErrorBar, self).__init__(opts, enabled)
        self.interval = interval
        self.chart_name = self._chart_name.format(int(interval*100))

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['low'] = list(df[self.opts.y]['mean'] * (1 + self.interval/2))
        result['high'] = list(df[self.opts.y]['mean'] * (1 - self.interval/2))
        return result


class ChartCI(AChart):
    _metrics = ['mean', 'ci']
    _chart_type = 'areasplinerange'
    _chart_name = '95% CI'

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['low'] = list(df[self.opts.y]['mean'] - df[self.opts.y]['ci'])
        result['high'] = list(df[self.opts.y]['mean'] + df[self.opts.y]['ci'])
        return result


class ChartSTD(AChart):
    _metrics = ['mean', 'std']
    _chart_type = 'areasplinerange'
    _chart_name = 'mean +- std'

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['low'] = list(df[self.opts.y]['mean'] - df[self.opts.y]['std'])
        result['high'] = list(df[self.opts.y]['mean'] + df[self.opts.y]['std'])
        return result


class ChartBoxPlot(AChart):
    _metrics = ['min', '25%', '50%', '75%', 'max']
    _chart_type = 'boxplot'
    _chart_name = 'boxplot'

    def _compute(self, df):
        result = df[self.opts.y].reset_index()[
            [self.opts.x, 'min', '25%', '50%', '75%', 'max']
        ]
        return result


class ChartLine(AChart):
    _metrics = ['mean']
    _chart_type = 'line'
    _chart_name = 'mean'

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['y'] = list(df[self.opts.y]['mean'])
        return result


class ChartGroup(object):
    y_metrics_default = {
        'mean': np.mean,
        'min': np.min,
        'max': np.max,
        'std': np.std,
        '25%': lambda x: np.percentile(x, 25),
        '50%': np.median,
        '75%': lambda x: np.percentile(x, 75),
        'ci': du.mean_confidence_interval,
    }

    def __init__(self, chart_options, options):
        self.line_chart = ChartLine(chart_options, options.get('show-mean', True))
        self.boxplot_chart = ChartBoxPlot(chart_options, options.get('show-boxplot', False))
        self.ci_chart = ChartCI(chart_options, options.get('show-ci', False))
        self.std_chart = ChartSTD(chart_options, options.get('show-stdbar', False))
        self.errorbar_chart = ChartErrorBar(chart_options, options.get('show-errorbar', False))

        self.all_charts = [
            self.line_chart, self.boxplot_chart, self.ci_chart,
            self.std_chart, self.errorbar_chart
        ]

        allowed = set([k for ch in self.all_charts for k in ch.get_metrics().keys()])
        self.y_metrics = {k: v for k, v in self.y_metrics_default.items() if k in allowed}

    def __bool__(self):
        for g in self.all_charts:
            if g:
                return True
        return False


class SparklineView(Resource):
    """
    a view which returns a list of chart configuration with data when called
    if no data matches the query, dict is returned with keys 'error' and 'description'
    """

    def _process_list_args(self, value):
        result: dict = dict([tuple(v.split('=')) for v in value])
        for k, v in result.items():
            if v.lower() == 'true':
                result[k] = True
            elif v.lower() == 'false':
                result[k] = False
            else:
                try:
                    result[k] = int(v)
                except:
                    result[k] = v
        return result

    def error_empty_df(self, filters):
        logger.info('empty result')
        return self.show_error(
            status=300,
            message='No results found',
            description='\n'.join([
                '<p>This usually means provided filters filtered out everything.</p>',
                '<p>DEBUG: The following filters were applied:</p>',
                '<pre><code>%s</code></pre>' % strings.to_json(filters)

            ])
        )

    def show_error(self, message, status=400, description=''):
        logger.info('error [%d] %s' % (status, message))
        return dict(
            status=status,
            message=message,
            description=description
        )

    def groupby(self, df, groupby):
        """
        :rtype: list[(list[str], list[str], list[str], pd.DataFrame)]
        """
        if not groupby:
            yield ('', '', '', df)
        else:

            keys = du.ensure_iterable(list(groupby.keys()))
            names = du.ensure_iterable(list(groupby.values()))

            for group_values, group_data in df.groupby(keys):
                yield (du.ensure_iterable(group_values), du.ensure_iterable(keys), du.ensure_iterable(names), group_data)

    def __init__(self):
        super(SparklineView, self).__init__()
        self.options = dict()
        self.config = None
        self.mongo = None

    def prepare(self, project, base64data=None):
        if base64data:
            self.options = json.loads(
                base64.decodebytes(base64data.encode()).decode()
            )
        else:
            logger.warning('no options given')
            self.options = dict()

        logger.info(strings.to_json(self.options), skip_format=True)

        self.config = ProjectConfig.get(project)
        self.mongo = CIHPCMongo.get(project)

    @Timer.decorate('Sparkline: get', logger.info)
    def get(self, project, base64data=''):
        self.prepare(project, base64data)

        mode = ViewMode(self.options.get('mode', {}).get('mode', ViewMode.SCALE_VIEW.value))
        squeeze = int(self.options.get('squeeze', {}).get('value', 1))
        interval = self.options.get('range', {})

        field_set = self.config.fields.required_fields()
        filter_dict = self.options['filters']

        if interval and 'from' in interval and 'to' in interval:
            filter_dict[self.config.fields.git.datetime.name] = {
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
                self.mongo.find_all(
                    db_find_filters,
                    db_find_fields,
                )
            )

            if data_frame.empty:
                return self.error_empty_df(db_find_filters)

            self.config.fields.apply_to_df(data_frame)
            data_frame[':merged:'] = 'g(?)'

        if mode is ViewMode.SCALE_VIEW:
            # split charts based on commit when in scale-view mode
            # if config.fields.git.datetime:
            #     config.test_view.groupby['git.datetime'] = 'date'
            # else:
            self.config.test_view.groupby['git.commit'] = 'commit'

            self.config.test_view.groupby = du.filter_values(
                self.config.test_view.groupby,
                forbidden=(self.config.fields.problem.size.name, self.config.fields.problem.cpu.name)
            )
            chart_options = du.dotdict(
                y=self.config.fields.result.duration.name,
                x=self.config.fields.problem.cpu.name,
                c=self.config.fields.git.commit.name,
                groupby={k: v for k,v in self.config.test_view.groupby.items() if self.options['groupby'].get(k, False)},
                colorby={k: v for k,v in self.config.test_view.groupby.items() if not self.options['groupby'].get(k, False)},
            )
            data_frame[chart_options.x] = data_frame[chart_options.x].apply(str)

        elif mode is ViewMode.TIME_SERIES:
            self.config.test_view.groupby['problem.cpu'] = 'cpu'
            self.config.test_view.groupby['problem.size'] = 'size'

            if self.config.fields.problem.test:
                self.config.test_view.groupby[self.config.fields.problem.test.name] = 'test'
                self.options['groupby'][self.config.fields.problem.test.name] = True

            if self.config.fields.problem.case:
                self.config.test_view.groupby[self.config.fields.problem.case.name] = 'size'
                self.options['groupby'][self.config.fields.problem.case.name] = True

            chart_options = du.dotdict(
                y=self.config.fields.result.duration.name,
                x=self.config.fields.git.datetime.name,
                c=self.config.fields.git.commit.name,
                groupby={k: v for k,v in self.config.test_view.groupby.items() if self.options['groupby'].get(k, False)},
                colorby={k: v for k,v in self.config.test_view.groupby.items() if not self.options['groupby'].get(k, False)},
            )
        else:
            raise Exception('Given mode is not supported %s' % mode)

        chart_group = ChartGroup(chart_options, self.options)
        if not chart_group:
            return self.show_error(
                status=300,
                message='No chart series selected',
                description='<p>All of the chart series are disabled, so no chart can be displayed. '
                            'Please enable at least one of the chart type series</p>'
                            '<a class="btn btn-warning" data-toggle="modal" data-target="#modal-options">Click here to open configuration.</a>'
            )

        charts = list()
        for group_values, group_keys, group_names, group_data in self.groupby(data_frame, chart_options.groupby):
            group_title = du.join_lists(group_names, group_values, '{} = <b>{}</b>', '<br />')

            series = list()
            extra = dict(size=list())
            colors_iter = iter(self.config.color_palette.copy() * 5)
            for color_values, color_keys, color_names, color_data in self.groupby(group_data, chart_options.colorby):
                color_title = du.join_lists(color_names, color_values, '{} = {}', ', ')
                if color_title == ' = ':
                    color_title = '*'
                color = next(colors_iter)

                if squeeze and squeeze > 1:
                    merge_unique = sorted(list(set(color_data[chart_options.x])))
                    merge_groups = np.repeat(np.arange(int(len(merge_unique)/squeeze + 1)), squeeze)
                    merge_unique_len = len(merge_unique)
                    merge_map = dict()
                    for i in range(merge_unique_len):
                        s = merge_groups[i]
                        bb, ee = s*squeeze+1, min((s+1)*squeeze, merge_unique_len)
                        b, e = merge_unique[bb-1], merge_unique[ee-1]
                        cnt = ee - (bb - 1)
                        if b == e:
                            merge_map[merge_unique[i]] = 'group %s (1 item, %s)' % (chr(65 + s), b)
                        else:
                            if isinstance(b, datetime.datetime):
                                duration = dateutils.human_interval(b, e)
                                merge_map[merge_unique[i]] = 'group %s (%d items, period of %s)' % (chr(65 + s), cnt, duration)
                            else:
                                merge_map[merge_unique[i]] = 'group %s (%d items, %s - %s)' % (chr(65+s), cnt, b, e)

                    # color_data[':merged:'] = color_data[chart_options.x].map(merge_map)
                    # TODO carefully think this through
                    color_data[chart_options.x] = color_data[chart_options.x].map(merge_map)
                    # chart_options.x = ':merged:'

                with Timer('agg ' + color_title, log=logger.info):
                    cd_group = color_data.groupby(chart_options.x).aggregate({
                        chart_options.c: lambda x: list(set(x)),
                        chart_options.y: chart_group.y_metrics.items(),
                        '_id': lambda x: list(set(x)),
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

                if chart_group.line_chart:
                    series.append(chart_group.line_chart.get_chart(
                        cd_group, color_title,
                        color=color(1.0),
                    ))

                if series:
                    series[-1]['extra'] = {
                        '_id': cd_group['_id'],
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
