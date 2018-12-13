#!/usr/bin/python
# author: Jan Hybs

import logging

from cihpc.core.structures.a_project import ComplexClass


logger = logging.getLogger(__name__)


class ProjectStepCache(ComplexClass):
    """
    A class which handles project caching
    """

    def __init__(self, kwargs):
        super(ProjectStepCache, self).__init__(kwargs)

        if not kwargs:
            self.directories = None
            self.storage = None
            self.fields = None

        elif isinstance(kwargs, dict):
            self.directories = kwargs['directories']  # required
            self.storage = kwargs.get('storage', '<os.HOME>/.cache/cihpc')  # default is home .cache dir
            self.fields = kwargs.get('fields', dict())

        elif isinstance(kwargs, list):
            self.storage = '<os.HOME>/.cache/cihpc'
            self.directories = kwargs
            self.fields = dict()

        elif isinstance(kwargs, str):
            self.enabled = True
            self.storage = '<os.HOME>/.cache/cihpc'
            self.directories = [kwargs]
            self.fields = dict()

        else:
            raise ValueError('kwargs must be dictionary, string or list')
