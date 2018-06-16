#!/usr/bin/python
# author: Jan Hybs

from utils.logging import logger
from structures import pick
from structures.project_step_git import ProjectStepGit
from structures.project_step_container import ProjectStepContainer
from structures.project_step_collect import ProjectStepCollect


class ProjectStep(object):
    """
    Class representing single step in a project
    """
    def __init__(self, **kwargs):
        self.name = kwargs['name']

        self.git = [ProjectStepGit(**x) for x in kwargs.get('git', [])]
        self.description = kwargs.get('description', [])
        self.enabled = kwargs.get('enabled', True)
        self.verbose = pick(kwargs, False, 'verbose', 'debug')
        self.container = ProjectStepContainer(**kwargs.get('container', {})) if kwargs.get('container', {}) else None

        self.shell = kwargs.get('shell', None)

        # build matrix
        self.variables = kwargs.get('variables', [])
        self.collect = ProjectStepCollect(**kwargs.get('collect', {})) if kwargs.get('collect', {}) else None