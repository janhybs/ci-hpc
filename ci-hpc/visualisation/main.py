#!/usr/bin/python3
# author: Jan Hybs

import os
import sys

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..',
        )
    )
)


from utils.logging import logger

import argparse


def parse_args():
    from utils.parsing import RawFormatter

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
    
    from visualisation.www import init_flask_server
    from visualisation.www.rest.sparkline_view import SparklineView
    from visualisation.www.rest.frame_view import FrameView
    from visualisation.www.rest.config_view import ConfigView
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
