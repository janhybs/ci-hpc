#!/usr/bin/python3
# author: Jan Hybs

from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from cihpc.utils.strings import JSONEncoder


def init_flask_server():
    app = Flask(__name__)
    app.config['RESTFUL_JSON'] = dict(
        cls=JSONEncoder
    )
    CORS(app)
    api = Api(app)
    return api, app
