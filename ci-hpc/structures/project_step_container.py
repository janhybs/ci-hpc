#!/usr/bin/python
# author: Jan Hybs


class ProjectStepContainer(object):
    """
    Helper class which holds information about singularity/docker
    """
    def __init__(self, value):
        self.exec = value  # lines to load container module and to exec singularity/docker

    def __bool__(self):
        return bool(self.exec)