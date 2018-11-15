#!/usr/bin/python
# author: Jan Hybs

import structures as structures_init
from structures.project_step_measure import ProjectStepMeasure
from structures import pick
from structures.project_step_git import ProjectStepGit
from structures.project_step_container import ProjectStepContainer
from structures.project_step_collect import ProjectStepCollect
from structures.project_step_parallel import ProjectStepParallel
from structures.project_step_repeat import ProjectStepRepeat
from utils.glob import global_configuration


class ProjectStep(object):
    """
    Class representing single step in a project

    :type section:          structures.project_section.ProjectSection
    :type git:              list[ProjectStepGit]
    :type description:      str
    :type enabled:          bool
    :type verbose:          bool
    :type container:        ProjectStepContainer
    :type smart_repeat:     ProjectStepRepeat
    :type repeat:           int
    :type shell:            str
    :type output:           str

    :type variables:        list
    :type measure:          ProjectStepMeasure
    :type collect:          ProjectStepCollect
    :type parallel:         ProjectStepParallel
    """
    def __init__(self, section, **kwargs):
        self.name = kwargs['name']

        self.git = [ProjectStepGit(**x) for x in kwargs.get('git', [])]
        self.description = kwargs.get('description', [])
        self.enabled = kwargs.get('enabled', True)
        self.verbose = pick(kwargs, False, 'verbose', 'debug')
        self.container = structures_init.new(kwargs, 'container', ProjectStepContainer)
        self.smart_repeat = ProjectStepRepeat(kwargs.get('repeat', 1))
        self.shell = kwargs.get('shell', None)
        self.parallel = ProjectStepParallel(**kwargs.get('parallel', dict()))

        self.output = kwargs.get(
            'output',
            'stdout' if global_configuration.tty else 'log+stdout'
        )

        # build matrix
        self.variables = kwargs.get('variables', [])

        # artifact generation
        self.measure = structures_init.new(kwargs, 'measure', ProjectStepMeasure)
        # artifact collection
        self.collect = structures_init.new(kwargs, 'collect', ProjectStepCollect)

        # project section
        self.section = section

        # save raw configuration
        self.raw_config = kwargs

        # if git repos were set, the first one is taken as
        # a project main git repository
        if self.git:
            global_configuration.project_repo = self.git[0].repo

    @property
    def ord_name(self):
        return '%d.%s' % (self.section.steps.index(self) + 1, self.name)

    @property
    def repeat(self):
        return self.smart_repeat.value
