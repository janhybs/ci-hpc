#!/usr/bin/python3
# author: Jan Hybs

import os, sys

from utils.logging import logger
from utils.glob import global_configuration
from utils.config import Config as cfg
cfg.init(global_configuration.cfg_path)

from visualisation.www import init_flask_server
from visualisation.www.rest.report import Report
from visualisation.www.rest.test_view import TestView
from visualisation.www.rest.frame_view import FrameView

# from visualisation.www.rest.case_view import init_case_view
# from visualisation.www.rest.case_view_detail import init_case_view_detail
# from visualisation.www.rest.tests import init_tests


api, app = init_flask_server()


api.add_resource(
    Report,
    '/<string:project>/report/<string:report_id>'
)

api.add_resource(
    TestView,
    '/<string:project>/case-view/<string:test_name>/<string:case_name>/<string:options>',
    '/<string:project>/case-view/<string:test_name>/<string:case_name>/',
)

api.add_resource(
    FrameView,
    '/<string:project>/case-view-detail/<string:ids>',
)


# init_report(api, app, m)
# init_case_view(api, app, m)
# init_tests(api, app, m)
# init_case_view_detail(api, app, m)

args = sys.argv[1:]
debug = True if args and args[0].lower() == 'debug' else False
debug = True

if __name__ == '__main__':
    app.run(debug=debug, host='0.0.0.0')
