#!/usr/bin/python3
# author: Jan Hybs

from flask_restful import Resource
import pandas as pd
import json
import utils.dateutils as dateutils

from visualisation.www.plot.highcharts import highcharts_frame_bar


def p(o):
    from utils.strings import JSONEncoder
    print(json.dumps(o, indent=True, cls=JSONEncoder))
    return o


def init_case_view_detail(api, app, m):
    class CaseViewDetail(Resource):
        # http://127.0.0.1:5000/case-view-detail/1add859ff7cb4470901cae269a987ef5

        def get(self, _id):
            result = list(
                m.client['flow123d']['reports'].aggregate(p([
                    {
                        '$match':
                            {
                                'problem.uuid': {'$in': _id.split(',')},
                            }
                    },
                    {
                        "$unwind": "$libs"
                    },
                    {
                        "$project": {
                            "_id": 0,
                            # "uuid": "$problem.uuid",
                            "path": "$timer.path",
                            "tag": "$timer.tag",
                            # 'git-branch': '$libs.branch',
                            # 'git-commit': '$libs.commit',
                            # 'git-timestamp': '$libs.timestamp',
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
            df['git-datetime'] = df['git-datetime'].apply(dateutils.long_format)
            a = highcharts_frame_bar(df)
            p(a)
            return a

    api.add_resource(CaseViewDetail, '/case-view-detail/<string:uuid>')