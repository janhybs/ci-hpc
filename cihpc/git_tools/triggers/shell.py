#!/bin/python3
# author: Jan Hybs


import logging


logger = logging.getLogger(__name__)

import os
import subprocess

from cihpc.cfg.config import global_configuration
from cihpc.git_tools.triggers import AbstractWebhookTrigger


class ShellTrigger(AbstractWebhookTrigger):

    def __init__(self, trigger_path=None):
        self.trigger_path = trigger_path
        self._process = None

    def process(self, payload):
        project = payload.repository.name
        commit = payload.after

        trigger_path = self.trigger_path or os.path.join(global_configuration.cwd, 'triggers', 'local-trigger')
        args = ['bash', trigger_path, project, commit]

        self._process = subprocess.Popen(args)

    def wait(self):
        self._process.wait()
        logger.info('trigger ended with %d' % self._process.returncode)
        return self._process.returncode

