#!/usr/bin/python3
# author: Jan Hybs

from flask_restful import Resource
from bson.objectid import ObjectId


def init_report(api, app, m):

    class Report(Resource):
        # http://127.0.0.1:5000/report/_id=5b27a7968ea11a3da0e5b668

        def get(self, report_id):
            conditions = dict([tuple(k.split('=')) for k in report_id.split(':')])
            if '_id' in conditions:
                conditions['_id'] = ObjectId(conditions['_id'])

            print(conditions)
            return m.client.flow123d.reports.find_one(conditions)

    api.add_resource(Report, '/report/<string:report_id>')