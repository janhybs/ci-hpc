#!/usr/bin/python3
# author: Jan Hybs

import argparse
import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_restful import Api

from cihpc.cfg.config import global_configuration
from cihpc.common.logging import basic_config
from cihpc.common.processing.daemon import Daemon
from cihpc.common.utils.strings import JSONEncoder


# -----------------------------------------------------------------


def init_flask_server():
    app = Flask(__name__)
    app.config['RESTFUL_JSON'] = dict(
        cls=JSONEncoder
    )
    CORS(app)
    # noinspection PyTypeChecker
    api = Api(app)
    return api, app


def parse_args(cmd_args=None):
    from cihpc.common.utils.parsing import RawFormatter

    # create parser
    parser = argparse.ArgumentParser(formatter_class=RawFormatter)
    parser.add_argument('--host', default="0.0.0.0", type=str, help='''R|
                            IP mask which this server will be available to.
                            By default the value is 0.0.0.0 meaning the server
                            will be reachable to anyone.
                            ''')
    parser.add_argument('-c', '--config-dir', default=None, help='''R|
                            A directory which www.yaml files for ALL projects will be served.
                            <CONFIG_DIR>/<PROJECT_NAME>/www.yaml is the full path the server
                            will be looking for
                            ''')
    parser.add_argument('-d', '--debug', default=False, action="store_true", help='''R|
                            Turns on the debug mode increasing verbosity.
                            ''')
    parser.add_argument('-p', '--port', default=5000, type=int, help='''R|
                            The port of the webserver. Defaults to 5000.
                            ''')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'debug'], help='''R|
                            Perform given action
                            ''')

    # parse given arguments
    args = parser.parse_args(cmd_args)
    return args


class WWWServer(Daemon):

    def __init__(self, name, flask_opts=None, **kwargs):
        """
        Parameters
        ----------
        name: str
            system unique name by which pid will be named
            usually corresponds to a project name

        flask_opts: dict or None
            additional options for the flask server

        kwargs: **dict
            additional arguments passed to the :class:`daemon.DaemonContext` constructor
        """

        super(WWWServer, self).__init__(
            name='WebhookService',
            pid_file='/tmp/%s.pid' % name,
            **kwargs
        )
        self.flask_opts = dict(
            host='0.0.0.0',
            port=5000,
            debug=False,
        )

        if flask_opts:
            self.flask_opts.update(flask_opts)

        self._app = None
        self._api = None

    # noinspection PyTypeChecker
    def run(self):
        basic_config()
        logger = logging.getLogger(__name__)

        from cihpc.www import init_flask_server
        from cihpc.www.rest.sparkline_view import SparklineView
        from cihpc.www.rest.frame_view import FrameView
        from cihpc.www.rest.config_view import ConfigView
        from cihpc.www.rest.commit_history_view import CommitHistoryView
        from flask import redirect

        api, app = init_flask_server()
        self._api = self._apps = api, app

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

        logger.info(
            'running server (debug: %s, host: %s, port: %d)',
            self.flask_opts.get('debug'),
            self.flask_opts.get('host'),
            self.flask_opts.get('port')
        )
        app.run(**self.flask_opts)
        logger.info('flask terminated')
        return app


def main(cmd_args=None):
    args = parse_args(cmd_args)
    basic_config()
    logger = logging.getLogger(__name__)

    if args.config_dir:
        global_configuration.update_cfg_path(args.config_dir)

    logger.info('Using config dir %s' % global_configuration.cfg)

    if args.action == 'debug':
        args.debug = True

    ws = WWWServer(
        'www-service',
        working_directory=os.getcwd(),
        flask_opts=dict(
            debug=args.debug,
            host=args.host,
            port=args.port,
        )
    )
    ws.do_action(args.action)
    return 0


if __name__ == '__main__':
    main()
