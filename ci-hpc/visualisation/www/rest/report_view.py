#!/usr/bin/python3
# author: Jan Hybs

from flask_restful import Resource
from bson.objectid import ObjectId
from artifacts.db.mongo import CIHPCMongo


class ReportView(Resource):
    # 127.0.0.1:5000/hello-world/report/_id=5b5edb03fa7f604fd1d1721a

    def get(self, project, report_id):
        mongo = CIHPCMongo.get(project)

        conditions = dict([tuple(k.split('=')) for k in report_id.split(':')])
        if '_id' in conditions:
            conditions['_id'] = ObjectId(conditions['_id'])

        return mongo.find_one(conditions)
