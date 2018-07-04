#!/usr/bin/python3
# author: Jan Hybs

from flask_restful import Resource
import pandas as pd


def init_tests(api, app, m):
    """
    :type m: artifacts.db.mongo.Mongo
    """

    class Tests(Resource):
        # http://127.0.0.1:5000/tests

        def get(self):
            result = list(
                m.client['flow123d']['reports'].aggregate(
                    [
                        {
                            '$group': {
                                '_id': {
                                    'test-name': '$problem.test-name',
                                },
                                'name': {
                                    '$first': '$problem.test-name'
                                },
                                'cases': {
                                    '$addToSet': '$problem.case-name'
                                }
                            }
                        }
                    ]
                )
            )
            df = pd.DataFrame(result).sort_values(by=['name'])
            del df['_id']
            return df.to_dict('records')

    api.add_resource(Tests, '/tests')
