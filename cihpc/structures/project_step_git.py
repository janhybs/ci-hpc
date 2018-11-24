#!/usr/bin/python
# author: Jan Hybs


import os
from cihpc.utils.logging import Logger
from cihpc.utils.files import StdoutType


class ProjectStepGit(object):
    """
    Simple class holding git specification
    """

    def __init__(self, url,
                 branch='master',
                 commit='',
                 logging=Logger.LEVEL_DEBUG,
                 stdout=StdoutType.DEVNULL,
                 **kwargs):

        self.url = url
        self.branch = branch
        self.commit = commit
        self.logging = logging
        self.stdout = stdout.value
        self.remove_before_checkout = kwargs.get('remove-before-checkout', False)

        self.repo = str(os.path.basename(self.url).split('.')[0])

        # optionally mark this repo as main
        if kwargs.get('is-main', False):
            from cihpc.cfg.config import global_configuration

            global_configuration.project_git = self

    def __repr__(self):
        return 'Git(repo=%s)' % self.repo
