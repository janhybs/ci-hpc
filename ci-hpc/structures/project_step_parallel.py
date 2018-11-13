#!/usr/bin/python
# author: Jan Hybs


import os

from utils.parallels import determine_cpus


class ProjectStepParallel(object):
    """
    Simple class holding git specification
    :type cpus: int
    :type prop: any
    """
    def __init__(self, **kwargs):
        self.enabled = bool(kwargs)
        self.prop = kwargs.get('prop', None)
        self.cpus = determine_cpus(
            kwargs.get('cpus', 1)
        )

    def __bool__(self):
        return self.enabled
