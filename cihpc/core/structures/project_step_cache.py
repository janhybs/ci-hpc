#!/usr/bin/python
# author: Jan Hybs

import logging

logger = logging.getLogger(__name__)


class ProjectStepCache(object):
    """
    A class which handles project caching
    """

    def __init__(self, kwargs):
        if not kwargs:
            self.enabled = False
            self.directories = None
            self.storage = None
            self.fields = None

        elif isinstance(kwargs, dict):
            self.enabled = True
            self.storage = kwargs['storage']  # required
            self.directories = kwargs['directories']  # required
            self.fields = kwargs.get('fields', dict())

        else:
            raise ValueError('kwargs must be dictionary')

    def __bool__(self):
        return self.enabled
