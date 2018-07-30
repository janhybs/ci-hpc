#!/bin/python3
# author: Jan Hybs

import argparse
from flask_restful import Resource
from artifacts.db.mongo import CIHPCMongo

import pandas as pd
import seaborn as sns

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
    def get(self, project, test_name=None, case_name=None, options=''):
        mongo = CIHPCMongo.get(project)

        opts = [] if not options else ('--' + str(options).replace(',', ' --')).split()
        args = parser.parse_args(opts)

        pipeline = mongo.pipeline
        match = {
            'problem.test-name': test_name,
            'problem.case-name': case_name,
        }

        pipeline = [{'$match': match}] + pipeline
        df = pd.DataFrame(list(mongo.aggregate(pipeline)))

        if df.empty:
            return dict(
                error='No data found',
                description='This usually means filters provided filtered out everything.'
        )
        df['git-timestamp'] = df['git-timestamp'] * 1000
        result = list()
        colors = sns.color_palette()

        clr = 'rgba({}, {}, {}, %f)'.format(*[int(x * 255) for x in colors[0]])
        result.append(dict(
            size=None,
            data=highcharts_frame_in_time(df, title='Benchmark %s/%s in time' % (test_name, case_name), color=clr % 1.0, args=args)
        ))

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

        return result