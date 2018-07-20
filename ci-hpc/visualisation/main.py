#!/usr/bin/python3
# author: Jan Hybs

import os, sys

from utils.logging import logger
from utils.config import Config as cfg

from visualisation.www import init_flask_server
from visualisation.www.rest.report import init_report
from visualisation.www.rest.case_view import init_case_view
from visualisation.www.rest.case_view_detail import init_case_view_detail
from visualisation.www.rest.tests import init_tests


__dir__ = os.path.abspath(os.path.dirname(__file__))
__root__ = os.path.dirname(os.path.dirname(__dir__))
__cfg__ = os.path.join(__root__, 'cfg')
secret_path = os.path.join(__cfg__, 'secret.yaml')

cfg.init(secret_path)
api, app, m = init_flask_server()


init_report(api, app, m)
init_case_view(api, app, m)
init_tests(api, app, m)
init_case_view_detail(api, app, m)

args = sys.argv[1:]
debug = True if args and args[0].lower() == 'debug' else False
debug = True

if __name__ == '__main__':
    app.run(debug=debug, host='0.0.0.0')
