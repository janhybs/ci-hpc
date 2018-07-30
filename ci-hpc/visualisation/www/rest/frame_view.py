#!/bin/python3
# author: Jan Hybs

import argparse
from flask_restful import Resource
from artifacts.db.mongo import CIHPCMongo

import pandas as pd
from bson.objectid import ObjectId
from artifacts.db.mongo import Fields as db

from utils import dateutils, strings
from visualisation.www.plot.highcharts import highcharts_frame_in_time, highcharts_frame_bar
from artifacts.collect.modules import unwind_reports

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
parser.add_argument('--group-by', type=str, default=None)


class FrameView(Resource):
    def get(self, project, ids,):
        mongo = CIHPCMongo.get(project)

        pipeline = mongo.pipeline
        match = {
            '_id': {'$in': [ObjectId(x) for x in ids.split(',')]},
        }

        args = parser.parse_args([])
        args.group_by = [db.GIT_DATETIME]
        args.rename = {
            'name': 'timer-name',
            'y': 'timer-duration',
            'path': 'timer-name',
        }

        pipeline = [{'$match': match}] + pipeline

        items = unwind_reports(list(mongo.aggregate(pipeline)), flatten=True)
        df = pd.DataFrame(items)

        if df.empty:
            return dict(
                error='No data found',
                description='This usually means filters provided filtered out everything.'
        )

        df['git-datetime'] = df['git-datetime'].apply(dateutils.long_format)
        result = highcharts_frame_bar(df, args)
        strings.to_json(result)
        return result

        # index = 0
        # for g, d in df.groupby('test-size'):
        #     clr = 'rgba({}, {}, {}, %f)'.format(*[int(x*255) for x in colors[index]])
        #
        #     if args.separate:
        #         result.append(dict(
        #             mesh=g,
        #             data=highcharts_frame_in_time(d, title='Mesh size %s' % g, color=clr % 1.0, args=args)
        #         ))
        #     else:
        #         if not result:
        #             result.append(dict(
        #                 mesh=g,
        #                 data=highcharts_frame_in_time(d, title='Mesh size %s' % g, color=clr % 1.0, args=args)
        #             ))
        #         else:
        #             r = highcharts_frame_in_time(d, title='Mesh size %s' % g, color=clr % 1.0, args=args)
        #             result[0]['data']['series'].extend(r['series'])
        #     index += 1
