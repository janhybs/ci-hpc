#!/bin/python3
# author: Jan Hybs
import datetime
from loguru import logger
import sys

from cihpc.cfg.cfgutil import find_valid_configuration




import argparse
import json
import os
import queue
import subprocess
import threading

from flask import Flask, request

from cihpc.cfg.config import global_configuration
from cihpc.common.processing.daemon import Daemon
from cihpc.common.utils.git.webhooks.push_hook import push_webhook_from_dict
from cihpc.common.utils.timer import Timer
from cihpc.git_tools.utils import (
    CommitBrowser,
    CommitPolicy,
    ArgConstructor,
    WebhookTrigger,
)


def parse_args():
    from cihpc.common.utils.parsing import RawFormatter

    # create parser
    parser = argparse.ArgumentParser(formatter_class=RawFormatter)
    parser.add_argument('--host', default="0.0.0.0", type=str, help='''R|
                            IP mask which this server will be available to.
                            By default the value is 0.0.0.0 meaning the server
                            will be reachable to anyone.
                            ''')
    parser.add_argument('-c', '--config-dir', type=str, default=None, help='''R|
                            Path to the directory, where webhook.yaml file is
                            located. If no value is set default value will current dir,
                            ''')
    parser.add_argument('-d', '--debug', default=False, action="store_true", help='''R|
                            Turns on the debug mode increasing verbosity.
                            ''')
    parser.add_argument('-p', '--port', default=5005, type=int, help='''R|
                            The port of the webserver. Defaults to 5000.
                            ''')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'debug'], help='''R|
                            Perform given action
                            ''')

    # parse given arguments
    args = parser.parse_args()
    return args


class CommitHistoryExecutor(Daemon):

    def __init__(self, name, args_constructor, commit_browser, **kwargs):
        """
        Parameters
        ----------
        name: str
            system unique name by which pid will be named
            usually corresponds to a project name

        args_constructor: cihpc.git_tools.utils.ArgConstructor
            an argument constructor instance which will generate
            arguments which will be passed to :class:`subprocess.Popen`

        commit_browser: cihpc.git_tools.utils.CommitBrowser
            a browser which will yield a Commit object which will be used to
            complete a arguments taken from args_constructor

        kwargs: dict
            additional arguments passed to the :class:`daemon.DaemonContext` constructor
        """

        super(CommitHistoryExecutor, self).__init__(
            name='CommitHistoryExecutor',
            pid_file='/tmp/%s.pid' % name,
            **kwargs
        )

        self.args_constructor = args_constructor
        self.commit_browser = commit_browser

    def run(self):
        self.commit_browser.load_commits()
        self.commit_browser.pick_commits()

        logger.info(f'starting commit processing')
        for commit in self.commit_browser.commits:
            logger.info(f'%s starting' % commit.short_format)

            with Timer(commit.short_format) as timer:
                args = self.args_constructor.construct_arguments(commit.hash)
                logger.info(f' '.join([str(x) for x in args]))
                process = subprocess.Popen(args, cwd=global_configuration.cwd)
                process.wait()

            logger.info(f'%s took %s [%d]' % (commit.short_format, timer.pretty_duration, process.returncode))


class WebhookService(Daemon):
    _welcome_message = '''
# Great!

## The server is up and running

It is awaiting the <code>GitHub</code> webhook events

 - `host` is set to **`{self.flask_opts[host]}`**
 - `port` is set to **`{self.flask_opts[port]}`**
 - `debug` is set to **`{self.flask_opts[debug]}`**

## Make sure you have your webhook set up properly

To turn the webhooks on, go to your github repository settings page, e.g.\n
  `https://github.com/`**`username`**`/`**`repository`**`/settings/hooks`
\n

Each time a webhook arrives it will run the following (assuming the new commit hash is `foobar` and the 
project is `foo`): \n
  `{example_command}`

## Useful links
 - [creating webhooks](https://developer.github.com/webhooks/creating/)
 - [what are webhooks](https://developer.github.com/v3/activity/events/types/#pushevent)

</html>
'''.strip()

    _welcome_html = '''
<!doctype html>
<html lang="en">
<head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css"
     integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
</head>
<body>
    <div class="jumbotron">
    %s
    </div>
</body>
</html>
    '''.strip()

    def __init__(self, name, webhook_trigger, flask_opts=None, **kwargs):
        """
        Parameters
        ----------
        name: str
            system unique name by which pid will be named
            usually corresponds to a project name

        flask_opts: dict or None
            additional options for the flask server

        webhook_trigger: cihpc.git_tools.utils.WebhookTrigger
            instance with method 'process' accepting webhook payloads

        kwargs: **dict
            additional arguments passed to the :class:`daemon.DaemonContext` constructor
        """

        super(WebhookService, self).__init__(
            name='WebhookService',
            pid_file='/tmp/%s.pid' % name,
            **kwargs
        )
        self.webhook_trigger = webhook_trigger

        self.flask_opts = dict(
            host='0.0.0.0',
            port=5001,
            debug=False,
        )

        if flask_opts:
            self.flask_opts.update(flask_opts)

        self._app = None
        self._queue = queue.Queue()
        self._worker_thread = None

    def _start_worker_thread(self):
        def process_items():
            while True:
                self._process_payload(self._queue.get())

        self._worker_thread = threading.Thread(target=process_items)
        self._worker_thread.start()

    def _process_payload(self, payload):
        """
        Popens a new process for the given payload

        Parameters
        ----------
        payload: cihpc.common.utils.git.webhooks.push_hook.PushWebhook

        Returns
        -------
        int
            return code of the process

        """

        logger.info(f'%s starting' % payload.after)

        with Timer(payload.after) as timer:
            try:
                returncode = self.webhook_trigger.process(payload)
                if returncode != 0:
                    raise Exception('script ended with non zero status')

            except Exception as e:
                # no such binary
                returncode = -1
                logger.exception('Error while starting the process %s' % self.webhook_trigger)

        logger.info(f'%s took %s [%d]' % (payload.after, timer.pretty_duration, returncode))

        return returncode

    def run(self):
        from loguru import logger

        

        logger.info(f'starting worker thread')
        self._start_worker_thread()

        app = Flask(self.name)
        self._app = app

        @app.route('/', methods=['GET'])
        def index():
            try:
                import markdown

                args = '$CIHPC_HOME/bin/cihpc -p foo --commit foobar'
                return (self._welcome_html % markdown.markdown(self._welcome_message)).format(
                    self=self,
                    example_command=args
                )
            except Exception as e:
                print(e)
                return 'The server is running'

        @app.route('/webhook', methods=['POST'])
        def webhook():
            try:
                payload_str = request.form['payload']
                payload = push_webhook_from_dict(json.loads(payload_str))
                self._queue.put(payload)
                msg = 'received new webhook %s -> %s from %s' % (
                    payload.before[:6],
                    payload.after[:6],
                    payload.head_commit.author.username,
                )
                logger.info(msg)
                return 'OK\n%s\n%s' % (msg, str(datetime.datetime.now()))
            except Exception as e:
                logger.exception('Payload parsing error')
                return 'There was an error during payload parse %s' % str(e.__class__), 404

        logger.info(
            'running server (debug: %s, host: %s, port: %d)',
            self.flask_opts.get('debug'),
            self.flask_opts.get('host'),
            self.flask_opts.get('port')
        )
        app.run(**self.flask_opts)
        logger.info(f'flask terminated')
        return app


def main():
    args = parse_args()
    project_dir = find_valid_configuration(
        args.config_dir,
        global_configuration.home,
        file='webhook.yaml',
        raise_if_not_found=True
    )

    if not project_dir:
        logger.error('termination execution')
        sys.exit(1)
    else:
        logger.debug(f'determined config dir: {project_dir}')
        global_configuration.project_cfg_dir = project_dir

    logger.info(f'running webhook server for the configuration \n{project_dir}')

    webhook_trigger = WebhookTrigger.from_file(os.path.join(project_dir, 'webhook.yaml'))

    ws = WebhookService(
        'webhook-service',
        webhook_trigger,
        working_directory=os.getcwd(),
        flask_opts=dict(
            debug=args.debug,
            host=args.host,
            port=args.port,
        )
    )
    ws.do_action(args.action)


if __name__ == '__main__':
    main()
