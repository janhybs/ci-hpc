#!/usr/bin/python
# author: Jan Hybs


import os


class ProjectStepGit(object):
    """
    Simple class holding git specification
    """
    def __init__(self, **kwargs):
        self.url = kwargs['url']
        self.repo = str(os.path.basename(self.url).split('.')[0])
        self.remove_before_checkout = kwargs.get('remove-before-checkout', False)
        self.branch = kwargs.get('branch', 'master')
        self.commit = kwargs.get('commit', '')
        self.logging = kwargs.get('logging', 'debug')
        self.stdout = kwargs.get('stdout', 'DEVNULL')

        # optionally mark this repo as main
        if kwargs.get('is-main', False):
            from utils.glob import global_configuration
            global_configuration.project_git = self

    def __repr__(self):
        return 'Git(repo=%s)' % self.repo