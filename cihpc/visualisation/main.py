#!/usr/bin/python3
# author: Jan Hybs
# from functools import lru_cache
# import time
#
#
# class A(object):
#     def __init__(self, a=None):
#         self.a = a
#
#     def __key(self):
#         return (self.a, )
#
#     def __hash__(self):
#         return hash(self.__key())
#
#     def __eq__(self, other):
#         return isinstance(self, type(other)) and self.__key() == other.__key()
#
#
# class B(object):
#     @lru_cache(maxsize=100)
#     def sparkline_view(self, *args, **kwargs):
#         print(time.time())
#         return None
#
# @lru_cache(maxsize=100)
# def sparkline_view(*args, **kwargs):
#     print(time.time())
#     return None
#
# a1= A(1)
# a2 = A(1)
# b = B()
#
# b.sparkline_view(a1)
# b.sparkline_view(a2)
# b.sparkline_view(3)
#
# print(b.sparkline_view.cache_info())
#
#
#
# exit(0)

import cihpc.utils.logging
from cihpc.cfg.config import global_configuration


cihpc.utils.logging.logger = cihpc.utils.logging.Logger.init(
    global_configuration.log_path,
    global_configuration.log_style,
    global_configuration.tty
)

from cihpc.artifacts.db.mongo import CIHPCMongo


mongo = CIHPCMongo.get('flow123d')
for item in mongo.reports.find():
    p = item['problem']
    if p.get('cpu') != int(p.get('cpus')):
        print(item)
        break

print(mongo)
exit(0)

import os
import sys
import argparse


sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..',
        )
    )
)

from cihpc.cfg.config import global_configuration
import cihpc.utils.logging


cihpc.utils.logging.logger = cihpc.utils.logging.Logger.init(
    global_configuration.log_path,
    global_configuration.log_style,
    global_configuration.tty
)

from cihpc.utils.logging import logger


def parse_args():
    from cihpc.utils.parsing import RawFormatter

    # create parser
    parser = argparse.ArgumentParser(formatter_class=RawFormatter)
    parser.add_argument('--host', default="0.0.0.0", type=str, help='''R|
                            IP mask which this server will be available to.
                            By default the value is 0.0.0.0 meaning the server
                            will be reachable to anyone.
                            ''')
    parser.add_argument('-d', '--debug', default=False, action="store_true", help='''R|
                            Turns on the debug mode increasing verbosity.
                            ''')
    parser.add_argument('-p', '--port', default=5000, type=int, help='''R|
                            The port of the webserver. Defaults to 5000.
                            ''')

    # parse given arguments
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    from cihpc.visualisation.www import init_flask_server
    from cihpc.visualisation.www.rest.sparkline_view import SparklineView
    from cihpc.visualisation.www.rest.frame_view import FrameView
    from cihpc.visualisation.www.rest.config_view import ConfigView
    from cihpc.visualisation.www.rest.commit_history_view import CommitHistoryView
    from flask import redirect

    api, app = init_flask_server()

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

    api.add_resource(
        CommitHistoryView,
        '/<string:project>/commit-history',
    )

    @app.route('/')
    def hello_world():
        return 'Your server is running!'

    @app.route('/<string:project>/badge')
    def badge(project, opts=''):
        shields = 'https://img.shields.io/badge'
        lbl = 'label=CI-HPC'
        style = 'style=flat-square'
        url = '%s/cihpc-%s-orange.svg?%s&%s' % (shields, project, lbl, style)
        return redirect(url)

    if not args.debug:
        logger.set_level('info')
    logger.set_level('info')

    logger.info('running server (debug: %s, host: %s, port: %d)', args.debug, args.host, args.port)
    app.run(debug=args.debug, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
