#!/usr/bin/python3
# author: Jan Hybs

import os, sys

from utils.logging import logger
from utils.glob import global_configuration
from utils.config import Config as cfg
cfg.init(global_configuration.cfg_path)

from visualisation.www import init_flask_server
from visualisation.www.rest.report_view import ReportView
from visualisation.www.rest.test_view import TestView
from visualisation.www.rest.frame_view import FrameView
from visualisation.www.rest.config_view import ConfigView


api, app = init_flask_server()


api.add_resource(
    ReportView,
    '/<string:project>/report/<string:report_id>'
)

api.add_resource(
    TestView,
    '/<string:project>/case-view/<string:test_name>/<string:case_name>/<string:options>',
    '/<string:project>/case-view/<string:test_name>/<string:case_name>',
    '/<string:project>/case-view/<string:test_name>/',
    '/<string:project>/case-view/',
)

api.add_resource(
    FrameView,
    '/<string:project>/case-view-detail/<string:ids>',
)
api.add_resource(
    ConfigView,
    '/<string:project>/config',
)


args = sys.argv[1:]
debug = True if args and args[0].lower() == 'debug' else False

if __name__ == '__main__':
    app.run(debug=debug, host='0.0.0.0')
