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

        if kwargs.get('is-main', False):
            from utils.glob import global_configuration
            global_configuration.project_repo = self.repo
