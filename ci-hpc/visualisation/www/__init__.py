#!/usr/bin/python3
# author: Jan Hybs

from flask import Flask
from flask_restful import Resource, Api
from artifacts.db import mongo
from bson import ObjectId
import datetime
import json
import utils.dateutils as dateutils
import numpy as np
import pandas as pd
from flask_cors import CORS


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, np.ndarray):
            return list(o)
        if isinstance(o, pd.Series):
            return list(o)
        if isinstance(o, pd.DataFrame):
            return o.values
        if isinstance(o, datetime.datetime):
            return dateutils.long_format(o)
        if hasattr(o, 'to_json'):
            return o.to_json()
            # return o.isoformat()
        return json.JSONEncoder.default(self, o)

def init_flask_server():

    app = Flask(__name__)
    app.config['RESTFUL_JSON'] = dict(
        cls=JSONEncoder
    )
    CORS(app)
    api = Api(app)
    m = mongo.Mongo()
    return api, app, m