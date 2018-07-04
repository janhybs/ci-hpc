#!/usr/bin/python3
# author: Jan Hybs

from flask_restful import Resource
import pandas as pd

from visualisation.www.plot.chartjs import chartjs_category_scatter

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
import utils.dates as dateutils
import pymongo

# http://127.0.0.1:5000/case-view/12_darcy_frac/11_exact_2d_nc_p0/failed
# http://127.0.0.1:5000/case-view/10_darcy/01_source
def init_case_view(api, app, m):
    """
    :type m: artifacts.db.mongo.Mongo
    """
    print('creating index')
    print(m.client['flow123d'].reports.create_index([
        ('problem.test-name', pymongo.ASCENDING),
        ('problem.case-name', pymongo.ASCENDING),
        ('timer.tag', pymongo.ASCENDING),
        ('problem.returncode', pymongo.ASCENDING),
    ]))

    class CaseView(Resource):
        # /case-view/10_darcy/01_source/failed

        def get(self, test_name, case_name, failed='nope'):
            # conditions = dict([tuple(k.split('=')) for k in report_id.split(':')])
            # if '_id' in conditions:
            #     conditions['_id'] = ObjectId(conditions['_id'])
            #
            # print(conditions)
            result = list(
                m.client['flow123d']['reports'].aggregate([
                    {'$match':
                        {
                            'problem.test-name': test_name,
                            'problem.case-name': case_name,
                            'timer.tag': 'Whole Program',
                            'problem.returncode': 1 if failed == 'failed' else 0,
                            'system.container': True,
                        }
                    },
                    {
                        "$unwind": "$libs"
                    },
                    {
                        "$project": {
                            "_id": 0,
                            # "uuid": "$problem.uuid",

                            # 'git-branch': '$libs.branch',
                            'git-commit': '$libs.commit',
                            # 'git-timestamp': '$libs.timestamp',
                            'git-datetime': '$libs.datetime',
                            # 'returncode': '$problem.returncode',

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
                ])
            )
            df = pd.DataFrame(result)
            print(df)
            df['git-datetime'] = df['git-datetime'].apply(dateutils.long_format)
            return chartjs_category_scatter(df)

    api.add_resource(
        CaseView,
        '/case-view/<string:test_name>/<string:case_name>/<string:failed>',
        '/case-view/<string:test_name>/<string:case_name>',
     )
