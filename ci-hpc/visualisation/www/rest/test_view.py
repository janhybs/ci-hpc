#!/bin/python3
# author: Jan Hybs

import argparse

import itertools

import time
from flask_restful import Resource
from artifacts.db.mongo import CIHPCMongo

import pandas as pd
import seaborn as sns

from utils import strings
from utils.datautils import ensure_iterable
from utils.logging import logger
from utils.timer import Timer
from visualisation.www.plot.cfg.project_config import ProjectConfig
from visualisation.www.plot.highcharts import highcharts_frame_in_time


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
parser.add_argument('--separate', type=str2bool, default=True)
parser.add_argument('--groupby', type=str, default=None)
parser.add_argument('--show-scale', type=str2bool, default=False)
parser.add_argument('-f', '--ff', action='append', default=[], dest='filters')


class TestView(Resource):
    """
    a view which returns a list of chart configuration with data when called
    if no data matches the query, dict is returned with keys 'error' and 'description'
    """

    @Timer.decorate('TestView: get', logger.info)
    def get(self, project, options=''):
        if options:
            options = ('--' + options.rstrip(',').replace(',', ' --')).split()
        else:
            options = []

        args = parser.parse_args(options)
        filters = dict([tuple(v.split('=')) for v in args.filters])

        with Timer('config init', log=logger.debug):
            mongo = CIHPCMongo.get(project)
            config = ProjectConfig.get(project)
            filters = config.test_view.get_filters(filters)
            projection = config.test_view.get_projection()

        if args.show_scale:
            x_prop = config.test_view.x_prop
            y_prop = config.test_view.y_prop
            c_prop = config.test_view.c_prop

            config.test_view.x_prop = c_prop
            config.test_view.c_prop = x_prop

        with Timer('db find:', log=logger.debug):
            data_frame = pd.DataFrame(
                mongo.find_all(
                    filters,
                    projection,
                )
            )

        if data_frame.empty:
            logger.info('empty result')
            return dict(
                error='No results found',
                description='\n'.join([
                    '<p>This usually means provided filters filtered out everything.</p>',
                    '<p>DEBUG: The following filters were applied:</p>',
                    '<pre><code>%s</code></pre>' % strings.to_json(filters)

                ])
            )

        if config.date_format:
            for col in data_frame.columns:
                if str(col).find('datetime') != -1:
                    data_frame[col] = data_frame[col].apply(config.date_format)

        groupby = list(config.test_view.groupby.values())

        # if we now cpu property and are plotting charts separately
        if config.test_view.c_prop and args.separate:
            groupby.append(config.test_view.c_prop)

        if not groupby:
            groups = [('all', data_frame)]
        else:
            groups = data_frame.groupby(groupby)

        charts = list()
        colors = config.color_palette.copy()

        with Timer('highcharts', log=logger.debug):
            for groupby_name, groupby_data in groups:

                # basic title
                title_dict = dict(zip(groupby, ensure_iterable(groupby_name)))

                if not args.separate and config.test_view.c_prop:
                    colors_iter = iter(colors)
                    series = list()

                    # scaling charts
                    colorby = [config.test_view.c_prop]
                    for colorby_name, colorby_data in groupby_data.groupby(colorby):
                        extra_title = dict(zip(colorby, ensure_iterable(colorby_name)))
                        title = ', '.join('%s=<b>%s</b>' % (str(k), str(v)) for k, v in title_dict.items())
                        color = next(colors_iter)(1.0)  # TODO cycle the colors

                        chart = highcharts_frame_in_time(
                            colorby_data,
                            config,
                            title=title,
                            color=color,
                            add_errorbar=False,
                            add_std=False,
                            metric_name='mean (%s)' % (', '.join('%s=%s' % (str(k), str(v)) for k, v in extra_title.items()))
                        )
                        series.extend(chart.series)

                    chart.series = series  # TODO check empty charts
                    charts.append(dict(
                        size=None,
                        data=chart
                    ))

                else:
                    title = ', '.join('%s=<b>%s</b>' % (str(k), str(v)) for k,v in title_dict.items())
                    color = strings.pick_random_item(colors, groupby_name)(1.0)

                    charts.append(dict(
                        size=None,
                        data=highcharts_frame_in_time(
                            groupby_data,
                            config,
                            title=title,
                            color=color
                        )
                    ))
        return charts
