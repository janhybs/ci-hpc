#!/bin/python3
# author: Jan Hybs

import argparse
import base64

import itertools
import json

import time

from bson import objectid
from flask_restful import Resource
from artifacts.db.mongo import CIHPCMongo

import pandas as pd
import numpy as np
import seaborn as sns

from utils import strings
from utils.datautils import ensure_iterable, dotdict
from utils.logging import logger
from utils.timer import Timer
from visualisation.www.plot.cfg.project_config import ProjectConfig, ViewMode
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



def _fillna(df):
    return df.where(pd.notnull(df), None)


class FrameView(Resource):
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
        return {k: v for k, v in obj.items() if v not in values}

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

    def _filter_keys(self, d, required=None, forbidden=None):
        if required:
            d = {k: v for k,v in d.items() if v in required}
        if forbidden:
            d = {k: v for k, v in d.items() if v not in forbidden}
        return d

    def _filter_values(self, d, required=None, forbidden=None):
        if required:
            d = {k: v for k,v in d.items() if k in required}
        if forbidden:
            d = {k: v for k, v in d.items() if k not in forbidden}
        return d

    def error_empty_df(self, filters):
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

    def groupby(self, df, groupby):
        """

        :rtype: list[(list[str], list[str], list[str], pd.DataFrame)]
        """
        if not groupby:
            yield ('', '', '', df)
        else:

            keys = ensure_iterable(list(groupby.keys()))
            names = ensure_iterable(list(groupby.values()))

            for group_values, group_data in df.groupby(keys):
                yield (ensure_iterable(group_values), ensure_iterable(keys), ensure_iterable(names), group_data)

    @Timer.decorate('Frameview: get', logger.info)
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

        config = ProjectConfig.get(project)
        _ids = [objectid.ObjectId(x) for y in options['_ids'] for x in y]

        field_set = config.fields.required_fields()
        filter_dict = options['filters']

        projection_list = set(filter_dict.keys()) | field_set
        projection_list.add(config.frame_view.unwind)
        db_find_fields = dict(zip(projection_list, itertools.repeat(1)))

        # add _ids to selector
        db_find_filters = self._filter_keys(
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
                return self.error_empty_df(db_find_filters)

            config.fields.apply_to_df(data_frame)


        chart_options = dotdict(
            y=config.frame_view.fields.timers.duration.name,
            x=config.frame_view.fields.timers.name.name,
            n=config.frame_view.fields.timers.path.name,
            groupby={},
            colorby=config.frame_view.groupby,
        )

        print(chart_options)

        charts = list()
        for group_values, group_keys, group_names, group_data in self.groupby(data_frame, chart_options.groupby):
            group_title = self._join_lists(group_names, group_values,'{} = <b>{}</b>', '<br />')

            series = list()
            colors_iter = iter(config.color_palette.copy() * 5)
            for color_values, color_keys, color_names, color_data in self.groupby(group_data, chart_options.colorby):
                color_title = self._join_lists(color_names, color_values, '{} = {}', ', ')
                color = next(colors_iter)

                print(color_title)

                with Timer('agg ' + color_title, log=logger.info):
                    # color_data = color_data.groupby(chart_options.x).agg({
                    #     chart_options.y: 'mean',
                    #     chart_options.n: 'first'
                    # }).sort_values(by=chart_options.y, ascending=False).head(50)

                    color_data = color_data.sort_values(by=chart_options.y, ascending=False).reset_index()

                    bar = pd.DataFrame()
                    bar['y'] = list(color_data[chart_options.x])
                    bar['x'] = list(color_data[chart_options.y])
                    series.append(dict(
                        type='scatter',
                        extra={
                            'path': color_data[chart_options.n],
                        },
                        data=_fillna(bar.round(3)),
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
