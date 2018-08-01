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
        # mongo = CIHPCMongo.get(project)
        #
        # items = list()
        # cursor = mongo.reports.find()
        # for item in cursor:
        #     del item['_id']
        #     item['problem']['case-name'] = 'io'
        #     item['result']['duration'] *= 100
        #     for i in range(len(item['timers'])):
        #         item['timers'][i]['duration'] *= 100
        #         item['timers'][i]['name'] = item['timers'][i]['name'].replace('mem_l', 'fs_cat_')
        #     items.append(item)
        #
        # # with open('backup.json', 'w') as fp:
        # #     fp.write(strings.to_json(items))
        # mongo.reports.insert_many(items)
        #
        # return items

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
        if not groupby:
            groups = [('all', data_frame)]
        else:
            groups = data_frame.groupby(groupby)

        charts = list()
        colors = iter(config.color_palette)

        for group_name, group_data in groups:
            title_dict = dict(zip(ensure_iterable(groupby), ensure_iterable(group_name)))
            title = ', '.join('%s=<b>%s</b>' % (str(k), str(v)) for k,v in title_dict.items())
            color = next(colors)(1.0)
            size = None if config.case_size_prop is None else group_name[:-1]
            charts.append(dict(
                size=size,
                data=highcharts_frame_in_time(
                    group_data,
                    config,
                    title=title,
                    color=color
                )
            ))

        return charts
