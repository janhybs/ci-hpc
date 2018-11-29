#!/usr/bin/python
# author: Jan Hybs


import os
import logging
from cihpc.common.utils.files import StdoutType


class ProjectStepGit(object):
    """
    Simple class holding git specification
    """

    def __init__(self, url,
                 branch='master',
                 commit='',
                 level='debug',
                 stdout=StdoutType.DEVNULL,
                 **kwargs):

        self.url = url
        self.branch = branch
        self.commit = commit
        self.logging = level
        self.stdout = stdout.value
        self.remove_before_checkout = kwargs.get('remove-before-checkout', False)

        self.repo = str(os.path.basename(self.url).split('.')[0])

        # optionally mark this repo as main
        if kwargs.get('is-main', False):
            from cihpc.cfg.config import global_configuration

            global_configuration.project_git = self

    def __repr__(self):
        return 'Git(repo=%s)' % self.repo
