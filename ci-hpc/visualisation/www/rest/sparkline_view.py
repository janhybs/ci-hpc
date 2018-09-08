#!/bin/python3
# author: Jan Hybs

import argparse
import base64

import itertools
import json

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
from visualisation.www.plot.highcharts import highcharts_sparkline_in_time


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


class SparklineView(Resource):
    """
    a view which returns a list of chart configuration with data when called
    if no data matches the query, dict is returned with keys 'error' and 'description'
    """

    def _process_list_args(self, value):
        result = dict([tuple(v.split('=')) for v in value])
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

    def _delete_from_dict(self, obj, *values):
        return {k: v for k,v in obj.items() if v not in values}

    def _join_dict(self, obj, format='{}={}', sep=','):
        return sep.join([format.format(k, v) for k,v in obj.items()])

    def _join_lists(self, keys, values, format='{}={}', sep=','):
        keys = ensure_iterable(keys)
        values = ensure_iterable(values)
        return sep.join([format.format(keys[i], values[i]) for i in range(len(keys))])

    def _split_groups_and_colors(self, config, options):
        """
        Determine which properties will cause separation into individual charts
        and which will cause new 'line' to appear within the same chart

        Parameters
        ----------
        config : ProjectConfig
        options : dict
        """
        group_map = {v: k for k, v in config.test_view.groupby.items()}
        possible_groups = config.test_view.groupby.values()
        wanted_groups = options['groups']

        final_groups = [x for x in possible_groups if wanted_groups.get(x, False)]
        final_groups_names = [group_map[x] for x in final_groups]
        final_colors = list(set(possible_groups) - set(final_groups))
        final_colors_names = [group_map[x] for x in final_colors]

        return final_groups, final_groups_names, final_colors, final_colors_names

    @Timer.decorate('Sparkline: get', logger.info)
    def get(self, project, base64data=''):
        if base64data:
            options = json.loads(
                base64.decodebytes(base64data.encode()).decode()
            )
        else:
            options = dict()

        print(
            strings.to_json(options)
        )

        scaling = False if options['scaling'] == 'none' else options['scaling']
        config = ProjectConfig.get(project)

        filters = {}
        for k in options['filters']:
            if k.startswith('.'):
                if k[1:] in config.test_view.groupby:
                    filters[config.test_view.groupby.get(k[1:])] = options['filters'][k]
            else:
                filters[k] = options['filters'][k]

        with Timer('config init', log=logger.debug):
            mongo = CIHPCMongo.get(project)
            filters = config.test_view.get_filters(filters)
            projection = config.test_view.get_projection()

        # with open('mongo.back.5.json', 'w') as fp:
        #     items = list(mongo.reports.find())
        #     fp.write(strings.to_json(items))
        #
        # for item in mongo.reports.find():
        #     item['problem']['weak'] = int(item['problem']['cpu']) == int(item['problem']['mesh'].split('_')[0])
        #     item['problem']['strong'] = int(item['problem']['cpu']) < int(item['problem']['mesh'].split('_')[0])
        #     print(mongo.reports.replace_one({'_id': item['_id']}, item))
        # return

        with Timer('db find:', log=logger.debug):
            data_frame = pd.DataFrame(
                mongo.find_all(
                    filters,
                    projection,
                )
            )
            # data_frame['git.timestamp'] *= 1000
            # print(data_frame.columns)
            # data_frame['problem.weak'] = data_frame.apply(
            #     lambda row: int(row['problem.cpu']) == int(row['problem.mesh'].split('_')[0])
            # )
            # data_frame['problem.strong'] = data_frame.apply(
            #     lambda row: int(row['problem.cpu']) <= int(row['problem.mesh'].split('_')[0])
            # )

        if data_frame.empty:
            logger.info('empty result')
            return dict(
                status=404,
                error='No results found',
                description='\n'.join([
                    '<p>This usually means provided filters filtered out everything.</p>',
                    '<p>DEBUG: The following filters were applied:</p>',
                    '<pre><code>%s</code></pre>' % strings.to_json(filters)

                ])
            )

        if scaling and config.test_view.c_prop:
            x_prop = config.test_view.x_prop
            y_prop = config.test_view.y_prop
            c_prop = config.test_view.c_prop
            s_prop = config.test_view.s_prop

            # x axis will now be cpu's
            config.test_view.x_prop = c_prop

            # when in scaling mode, we are not grouping based on CPU used (that is x axis now)
            # instead we group by commits
            config.test_view.groupby = self._delete_from_dict(config.test_view.groupby, c_prop)
            config.test_view.groupby['hash'] = x_prop

            if scaling == 'weak' and config.test_view.s_prop:
                config.test_view.groupby = self._delete_from_dict(config.test_view.groupby, s_prop)

        charts = list()
        color_pallete = config.color_palette.copy() * 5
        final_groups, final_groups_names, final_colors, final_colors_names =\
            self._split_groups_and_colors(config, options)

        if final_groups:
            groups = data_frame.groupby(final_groups)
        else:
            groups = [('*', data_frame)]

        for groupby_name, groupby_data in groups:
            groupby_title = self._join_lists(
                final_groups_names, groupby_name,
                '{} = <b>{}</b>', '<br />'
            )
            colors_iter = iter(color_pallete)

            if final_colors:
                colors = groupby_data.groupby(final_colors)
            else:
                colors = [('*', groupby_data)]

            series = []
            # print(groupby_title)
            for colorby_name, colorby_data in colors:
                colorby_title = self._join_lists(final_colors_names, colorby_name)
                # print('   ', colorby_title, colorby_data.shape)

                chart = highcharts_sparkline_in_time(
                    colorby_data,
                    config,
                    title=groupby_title,
                    color=next(colors_iter),
                    add_errorbar=options['show-errorbar'],
                    add_std=options['show-boxplot'],
                    metric_name='mean %s' % colorby_title
                )
                series.extend(chart.series)

            chart.series = series  # TODO check empty charts
            charts.append(dict(
                size=None,
                data=chart
            ))

        return dict(
            status=200,
            data=charts
        )

        # with open('mongo.back.json', 'w') as fp:
        #     items = list(mongo.reports.find())
        #     fp.write(strings.to_json(items))
        # return

        # result = list()
        # import datetime, time, copy
        # d1 = datetime.datetime(2018, 7, 15, 15, 45, 59)
        # d2 = datetime.datetime(2018, 7, 19, 12, 24, 59)
        # d3 = datetime.datetime(2018, 7, 28, 18, 13, 59)
        # d4 = datetime.datetime(2018, 8, 2, 11, 30, 59)
        # cm = [
        #     '3a31eb8373c092bbc1fdcd16c2103c1c1c32bae3',
        #     '503469ae8a32154aaa0e17728a70e1e8de3281cd',
        #     'be59f6e6ee1b1786a7a5d394d54ac88dd13b3975',
        #     '4893f3a46b7650fa8ec156c5976fee4e6aa6a43b',
        # ]
        # ms = [1.5, 1.2, 0.8, 1.1]
        # ds = [d1, d2, d3, d4]
        #
        # for item in mongo.reports.find():
        #     del item['_id']
        #
        #     for j in range(4):
        #         i = copy.deepcopy(item)
        #         i['git']['commit'] = cm[j]
        #         i['git']['datetime'] = ds[j]
        #         i['result']['duration'] *= ms[j]
        #         print(i['git']['datetime'])
        #         result.append(i)
        #
        # mongo.reports.insert_many(result)
        # for item in mongo.reports.find():
        #     print(item['git']['datetime'])
        # print(ds)
        # return

        # if args.show_scale:
        #     x_prop = config.test_view.x_prop
        #     y_prop = config.test_view.y_prop
        #     c_prop = config.test_view.c_prop
        #
        #     config.test_view.x_prop = c_prop
        #     config.test_view.c_prop = x_prop
        #
        # with Timer('db find:', log=logger.debug):
        #     data_frame = pd.DataFrame(
        #         mongo.find_all(
        #             filters,
        #             projection,
        #         )
        #     )
        #
        # if data_frame.empty:
        #     logger.info('empty result')
        #     return dict(
        #         status=404,
        #         error='No results found',
        #         description='\n'.join([
        #             '<p>This usually means provided filters filtered out everything.</p>',
        #             '<p>DEBUG: The following filters were applied:</p>',
        #             '<pre><code>%s</code></pre>' % strings.to_json(filters)
        #
        #         ])
        #     )
        #
        # if config.date_format:
        #     for col in data_frame.columns:
        #         if str(col).find('datetime') != -1:
        #             data_frame[col] = data_frame[col].apply(config.date_format)
        #
        # groupby = [x for x in config.test_view.groupby.values() if _groups.get(x, False)]
        #
        # print(_groups)
        # print(groupby)
        #
        # # if we know cpu property and are plotting charts separately
        # if config.test_view.c_prop and args.separate:
        #     groupby.append(config.test_view.c_prop)
        #
        # if not groupby:
        #     groups = [('all', data_frame)]
        # else:
        #     groups = data_frame.groupby(groupby)
        #
        # charts = list()
        # colors = config.color_palette.copy()
        #
        # with Timer('highcharts', log=logger.debug):
        #     for groupby_name, groupby_data in groups:
        #
        #         # basic title
        #         title_dict = dict(zip(groupby, ensure_iterable(groupby_name)))
        #
        #         if not args.separate and config.test_view.c_prop:
        #             colors_iter = iter(colors)
        #             series = list()
        #
        #             # scaling charts
        #             colorby = [config.test_view.c_prop]
        #             for colorby_name, colorby_data in groupby_data.groupby(colorby):
        #                 extra_title = dict(zip(colorby, ensure_iterable(colorby_name)))
        #                 title = ', '.join('%s=<b>%s</b>' % (str(k), str(v)) for k, v in title_dict.items())
        #                 color = next(colors_iter)(1.0)  # TODO cycle the colors
        #
        #                 chart = highcharts_sparkline_in_time(
        #                     colorby_data,
        #                     config,
        #                     title=title,
        #                     color=color,
        #                     add_errorbar=False,
        #                     add_std=False,
        #                     metric_name='mean (%s)' % (', '.join('%s=%s' % (str(k), str(v)) for k, v in extra_title.items()))
        #                 )
        #                 series.extend(chart.series)
        #
        #             chart.series = series  # TODO check empty charts
        #             charts.append(dict(
        #                 size=None,
        #                 data=chart
        #             ))
        #
        #         else:
        #             title = ', '.join('%s=<b>%s</b>' % (str(k), str(v)) for k,v in title_dict.items())
        #             color = strings.pick_random_item(colors, groupby_name)(1.0)
        #
        #             charts.append(dict(
        #                 size=None,
        #                 data=highcharts_sparkline_in_time(
        #                     groupby_data,
        #                     config,
        #                     title=title,
        #                     color=color
        #                 )
        #             ))
        #
        # return dict(
        #     status=200,
        #     data=charts
        # )
