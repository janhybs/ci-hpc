#!/usr/bin/python
# author: Jan Hybs


class ProjectStepContainer(object):
    """
    Helper class which holds information about singularity/docker
    """
    def __init__(self, **kwargs):
        self.load = kwargs.get('load', None)  # load module
        self.exec = kwargs.get('exec', None)  # command to exec singularity

    def __bool__(self):
        return bool(self.exec)