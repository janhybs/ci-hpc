#!/bin/python3
# author: Jan Hybs

import argparse
from flask_restful import Resource
from artifacts.db.mongo import CIHPCMongo

import pandas as pd
import seaborn as sns

from utils import strings
from utils.datautils import ensure_iterable
from utils.logging import logger
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


class TestView(Resource):
    """
    a view which returns a list of chart configuration with data when called
    if no data matches the query, dict is returned with keys 'error' and 'description'
    """

    def get(self, project, test_name=None, case_name=None, options=''):

        if options:
            options = ('--' + options.replace(',', ' --')).split()
        else:
            options = []

        args = parser.parse_args(options)
        mongo = CIHPCMongo.get(project)
        config = ProjectConfig.get(project)
        match = config.get_match_section(test_name, case_name)

        # construct pipeline from mongo config and project config
        pipeline = [match] + mongo.pipeline

        data_frame = pd.DataFrame(list(mongo.aggregate(pipeline)))

        if data_frame.empty:
            logger.info('empty result')
            return dict(
                error='No results found',
                description='\n'.join([
                    '<p>This usually means provided filters filtered out everything.</p>',
                    '<p>DEBUG: The following filters were applied:</p>',
                    '<pre><code>%s</code></pre>' % strings.to_json(match)

                ])
            )

        if config.date_format:
            for col in data_frame.columns:
                if str(col).find('datetime') != -1:
                    data_frame[col] = data_frame[col].apply(config.date_format)

        groupby = config.test_view.groupby

        colorby = ensure_iterable(config.test_view.colorby)
        if colorby and args.separate:
            groupby.extend(colorby)
            colorby = []

        if not groupby:
            groups = [('all', data_frame)]
        else:
            groups = data_frame.groupby(groupby)

        charts = list()
        colors = config.color_palette.copy()

        for groupby_name, groupby_data in groups:

            # basic title
            title_dict = dict(zip(ensure_iterable(groupby), ensure_iterable(groupby_name)))
            size = None if config.case_size_prop is None else groupby_name[:-1]

            if not args.separate and config.test_view.colorby:
                colors_iter = iter(colors)
                series = list()

                for colorby_name, colorby_data in groupby_data.groupby(config.test_view.colorby):
                    extra_title = dict(zip(ensure_iterable(colorby), ensure_iterable(colorby_name)))
                    title_dict.update(
                        extra_title
                    )
                    title = ', '.join('%s=<b>%s</b>' % (str(k), str(v)) for k, v in title_dict.items())
                    color = next(colors_iter)(1.0)  # TODO cycle the colors

                    chart = highcharts_frame_in_time(
                        colorby_data,
                        config,
                        title=title,
                        color=color,
                        add_errorbar=False,
                        add_std=False,
                        metric_name='mean %s' % (', '.join('%s=<b>%s</b>' % (str(k), str(v)) for k, v in extra_title.items()))
                    )
                    series.extend(chart.series)

                chart.series = series
                charts.append(dict(
                    size=size,
                    data=chart
                ))

            else:
                title = ', '.join('%s=<b>%s</b>' % (str(k), str(v)) for k,v in title_dict.items())
                color = strings.pick_random_item(colors, groupby_name)(1.0)

                charts.append(dict(
                    size=size,
                    data=highcharts_frame_in_time(
                        groupby_data,
                        config,
                        title=title,
                        color=color
                    )
                ))

        return charts
