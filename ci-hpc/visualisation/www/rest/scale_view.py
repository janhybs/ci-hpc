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
from utils.datautils import ensure_iterable, filter_rows
from utils.logging import logger
from utils.timer import Timer
from visualisation.www.plot.cfg.project_config import ProjectConfig
from visualisation.www.plot.highcharts import highcharts_sparkline_in_time


class ScaleView(Resource):

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

    @Timer.decorate('Scale: get', logger.info)
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

        print(config.fields)
        return

        filters = {}
        for k in options['filters']:
            if k.startswith('.'):
                if k[1:] in config.scale_view.groupby:
                    filters[config.scale_view.groupby.get(k[1:])] = options['filters'][k]
            else:
                filters[k] = options['filters'][k]

        with Timer('config init', log=logger.debug):
            mongo = CIHPCMongo.get(project)
            filters = config.scale_view.get_filters(filters)
            projection = config.scale_view.get_projection()
            print(projection)

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
                status=404,
                error='No results found',
                description='\n'.join([
                    '<p>This usually means provided filters filtered out everything.</p>',
                    '<p>DEBUG: The following filters were applied:</p>',
                    '<pre><code>%s</code></pre>' % strings.to_json(filters)

                ])
            )
        else:
            print(data_frame.head())

        x_prop = config.scale_view.x_prop
        y_prop = config.scale_view.y_prop
        c_prop = config.scale_view.c_prop
        s_prop = config.scale_view.s_prop


        # TODO fix scale_view and test_view
        # duration will remain on y axis
        config.test_view.y_prop = y_prop
        # on x axis will be cpu value
        config.test_view.x_prop = c_prop

        # when in scaling mode, we are not grouping based on CPU used (that is x axis now)
        # instead we group by commits
        config.scale_view.groupby = self._delete_from_dict(config.scale_view.groupby, s_prop, c_prop)
        config.scale_view.groupby['hash'] = x_prop

        charts = list()
        color_pallete = config.color_palette.copy() * 50
        final_groups, final_groups_names, final_colors, final_colors_names =\
            self._split_groups_and_colors(config, options)

        final_groups = ['git.datetime']
        final_groups_names = ['date']

        if final_groups:
            groups = data_frame.groupby(final_groups)
        else:
            groups = [('*', data_frame)]

        for groupby_name, groupby_data in groups:
            groupby_title = _join_lists(
                final_groups_names, groupby_name,
                '{} = <b>{}</b>', '<br />'
            )
            colors_iter = iter(color_pallete)

            if final_colors:
                colors = groupby_data.groupby(final_colors)
            else:
                colors = [('*', groupby_data)]

            series = []
            print(groupby_title)
            for colorby_name, colorby_data in colors:
                colorby_title = _join_lists(final_colors_names, colorby_name)
                print('   ', colorby_title, colorby_data.shape)

                for s in config.scale_view.series:
                    series_data = filter_rows(colorby_data, **s['filters'])

                    chart = highcharts_sparkline_in_time(
                        series_data,
                        config,
                        title=groupby_title,
                        color=next(colors_iter),
                        add_errorbar=options['show-errorbar'],
                        add_std=options['show-boxplot'],
                        metric_name=s['name'],
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

        return [x_prop, y_prop, c_prop, s_prop]