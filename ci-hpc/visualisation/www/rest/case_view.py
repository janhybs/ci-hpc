#!/usr/bin/python3
# author: Jan Hybs


from flask_restful import Resource
import pandas as pd
import json

from visualisation.www.plot.chartjs import chartjs_category_scatter
from visualisation.www.plot.highcharts import highcharts_frame_in_time

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
import pymongo
import argparse
import seaborn as sns


def str2bool(v):
    if v.lower() in ('yes', 'true', '1'):
        return True
    elif v.lower() in ('no', 'false', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def p(o):
    from utils.strings import JSONEncoder
    print(json.dumps(o, indent=True, cls=JSONEncoder))
    return o




# http://127.0.0.1:5000/case-view/12_darcy_frac/11_exact_2d_nc_p0/failed
# http://127.0.0.1:5000/case-view/10_darcy/01_source
def init_case_view(api, app, m):
    """
    :type m: artifacts.db.mongo.Mongo
    """
    # indexes = [
    #     'problem.test-name_1_problem.case-name_1_timer.tag_1_problem.returncode_1',
    #     'problem.test-name_1_problem.case-name_1_timer.tag_1_problem.returncode_1_problem.tags_1',
    #     'problem.test-name_1_problem.case-name_1_timer.tag_1_problem.returncode_1_problem.tags_1_system.tags_1',
    # ]
    # for i in indexes:
    #     print(m.client['flow123d']['reports'].drop_index(i))

    # for index in m.client['flow123d']['reports'].list_indexes():
    #     print(index)

    # m.client['flow123d']['reports'].drop_index('main-multi-index')
    print('creating index')
    print(m.client['flow123d']['reports'].create_index([
        ('problem.test-name', pymongo.ASCENDING),
        ('problem.case-name', pymongo.ASCENDING),
        ('timer.tag', pymongo.ASCENDING),
        ('problem.returncode', pymongo.ASCENDING),
        ('problem.tags', pymongo.ASCENDING),
        ('system.tag', pymongo.ASCENDING),
        ('system.mesh', pymongo.ASCENDING),
        ('system.benchmark', pymongo.ASCENDING),
    ], name='main-multi-index'))

    parser = argparse.ArgumentParser()
    parser.add_argument('--failed', type=str2bool, default=False)
    parser.add_argument('--uniform', type=str2bool, default=True)
    parser.add_argument('--smooth', type=str2bool, default=True)
    parser.add_argument('--separate', type=str2bool, default=True)

    class CaseView(Resource):
        # /case-view/10_darcy/01_source/failed

        def get(self, test_name, case_name, options=''):
            # conditions = dict([tuple(k.split('=')) for k in report_id.split(':')])
            # if '_id' in conditions:
            #     conditions['_id'] = ObjectId(conditions['_id'])
            #
            # print(conditions)

            opts = [] if not options else ('--' + str(options).replace(',', ' --')).split()
            args = parser.parse_args(opts)

            result = list(
                m.client['flow123d']['reports'].aggregate(p([
                    {'$match':
                        {
                            'problem.test-name': test_name,
                            'problem.case-name': case_name,
                            'timer.tag': 'Whole Program',
                            'problem.returncode': 1 if args.failed else 0,
                            # 'system.container': True,
                        }
                    },
                    {
                        "$unwind": "$libs"
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "uuid": "$problem.uuid",

                            # 'git-branch': '$libs.branch',
                            'git-commit': '$libs.commit',
                            'git-timestamp': '$libs.timestamp',
                            'git-datetime': '$libs.datetime',
                            # 'returncode': '$problem.returncode',

                            "test-size": "$problem.task-size",
                            # "test-name": "$problem.test-name",
                            # "case-name": "$problem.case-name",
                            # "cpu": "$problem.cpu",
                            # "nodename": "$problem.nodename",
                            # "test-size": "$problem.task-size",
                            # "machine": "$system.machine",
                            # 'frame': '$timer.tag',
                            'duration': '$timer.cumul-time-max',
                        }
                    },
                ]))
            )
            df = pd.DataFrame(result)
            if df.empty:
                return dict(
                    error='No data found',
                    description='This usually means filters provided filtered out everything.'
                )

            # df['git-datetime'] = df['git-datetime'].apply(dateutils.human_format2)
            df['git-timestamp'] = df['git-timestamp'] * 1000
            # df = df.sort_values(by='git-timestamp').reset_index(drop=True)
            result = list()
            index = 0
            colors = sns.color_palette()
            for g, d in df.groupby('test-size'):
                clr = 'rgba({}, {}, {}, %f)'.format(*[int(x*255) for x in colors[index]])

                if args.separate:
                    result.append(dict(
                        mesh=g,
                        data=highcharts_frame_in_time(d, title='Mesh size %s' % g, color=clr % 1.0, args=args)
                    ))
                else:
                    if not result:
                        result.append(dict(
                            mesh=g,
                            data=highcharts_frame_in_time(d, title='Mesh size %s' % g, color=clr % 1.0, args=args)
                        ))
                    else:
                        r = highcharts_frame_in_time(d, title='Mesh size %s' % g, color=clr % 1.0, args=args)
                        result[0]['data']['series'].extend(r['series'])
                index += 1
            p(result)
            return result
            # return highcharts_frame_in_time(df)
            # return chartjs_category_scatter(df)

    api.add_resource(
        CaseView,
        '/case-view/<string:test_name>/<string:case_name>/<string:options>',
        '/case-view/<string:test_name>/<string:case_name>',
     )