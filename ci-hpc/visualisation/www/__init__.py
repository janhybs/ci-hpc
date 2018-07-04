#!/usr/bin/python3
# author: Jan Hybs

from flask import Flask
from flask_restful import Resource, Api
from artifacts.db import mongo
from bson import ObjectId
import datetime
import json
import utils.dates as dateutils
import numpy as np
from flask_cors import CORS


def init_flask_server():
    class JSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, ObjectId):
                return str(o)
            if isinstance(o, np.ndarray):
                return list(o)
            if isinstance(o, datetime.datetime):
                return dateutils.long_format(o)
                # return o.isoformat()
            return json.JSONEncoder.default(self, o)

    app = Flask(__name__)
    app.config['RESTFUL_JSON'] = dict(
        cls=JSONEncoder
    )
    CORS(app)
    api = Api(app)
    m = mongo.Mongo()
    return api, app, m