#!/usr/bin/python3
# author: Jan Hybs

import os, sys

from utils.logging import logger

from visualisation.www import init_flask_server
from visualisation.www.rest.report_view import ReportView
from visualisation.www.rest.test_view import TestView
from visualisation.www.rest.sparkline_view import SparklineView
from visualisation.www.rest.scale_view import ScaleView
from visualisation.www.rest.frame_view import FrameView
from visualisation.www.rest.config_view import ConfigView


api, app = init_flask_server()


# api.add_resource(
#     ReportView,
#     '/<string:project>/report/<string:report_id>'
# )
#
# api.add_resource(
#     TestView,
#     '/<string:project>/case-view/<string:options>',
#     '/<string:project>/case-view',
# )
#
# api.add_resource(
#     ScaleView,
#     '/<string:project>/scale-view/<string:base64data>',
#     '/<string:project>/scale-view',
# )
#
# api.add_resource(
#     FrameView,
#     '/<string:project>/case-view-detail/<string:ids>',
# )


api.add_resource(
    SparklineView,
    '/<string:project>/sparkline-view/<string:base64data>',
    '/<string:project>/sparkline-view',
)

api.add_resource(
    FrameView,
    '/<string:project>/frame-view/<string:base64data>',
    '/<string:project>/frame-view',
)

api.add_resource(
    ConfigView,
    '/<string:project>/config',
)


@app.route('/')
def hello_world():
    return 'Your server is running!'


args = sys.argv[1:]
debug = True if args and args[0].lower() == 'debug' else False

if not debug:
    logger.set_level('info')
logger.set_level('info')

if __name__ == '__main__':
    logger.debug('running server')
    app.run(debug=debug, host='0.0.0.0')
