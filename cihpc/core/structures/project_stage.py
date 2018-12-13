#!/bin/python3
# author: Jan Hybs

import cihpc.common.utils.strings as strings
from cihpc.cfg.config import global_configuration
from cihpc.core.structures.a_project import ComplexClass
from cihpc.core.structures.project_step_cache import ProjectStepCache
from cihpc.core.structures.project_step_collect import ProjectStepCollect
from cihpc.core.structures.project_step_container import ProjectStepContainer
from cihpc.core.structures.project_step_git import ProjectStepGits
from cihpc.core.structures.project_step_measure import ProjectStepMeasure
from cihpc.core.structures.project_step_parallel import ProjectStepParallel
from cihpc.core.structures.project_step_repeat import ProjectStepRepeat
from cihpc.core.structures.project_step_variables import ProjectStepVariables


class Props(object):
    NAME = 'name'
    DESCRIPTION = 'description'
    ENABLED = 'enabled'
    GIT = 'git'
    CACHE = 'cache'
    SHELL = 'shell'
    OUTPUT = 'output'
    REPEAT = 'repeat'
    PARALLEL = 'parallel'
    VARIABLES = 'variables'
    COLLECT = 'collect'
    MEASURE = 'measure'
    CONTAINER = 'container'


class ProjectStages(list):

    def __init__(self, kwargs):
        super(ProjectStages, self).__init__()
        if not kwargs:
            return

        if isinstance(kwargs, list):
            for i, v in enumerate(kwargs):
                stage = ProjectStage(v)
                stage.index = i + 1
                self.append(stage)


class ProjectStage(ComplexClass):
    """
    :type gits: list[cihpc.core.structures.project_step_git.ProjectStepGit]
    """
    def __init__(self, kwargs):
        super(ProjectStage, self).__init__(kwargs)
        if not self:
            return

        elif isinstance(kwargs, dict):
            self.name = kwargs.get(Props.NAME)
            self._secure_name = strings.secure_filename(self.name)
            self.description = kwargs.get(Props.DESCRIPTION)
            self._enabled = kwargs.get(Props.ENABLED, True)

            # save raw configuration
            self.raw_config = kwargs

            if not self:
                return

            # output level
            self.output = kwargs.get(Props.OUTPUT, 'stdout' if global_configuration.tty else 'log+stdout')
            # caching
            self.cache = ProjectStepCache(kwargs.get(Props.CACHE))
            # list of git repos
            self.gits = ProjectStepGits(kwargs.get(Props.GIT))

            self.shell = kwargs.get(Props.SHELL)

            # repetition
            self.smart_repeat = ProjectStepRepeat(kwargs.get(Props.REPEAT))
            # parallel processing
            self.parallel = ProjectStepParallel(kwargs.get(Props.PARALLEL))
            # variable product
            self.variables = ProjectStepVariables(kwargs.get(Props.VARIABLES))
            # optional containerization
            self.container = ProjectStepContainer(kwargs.get(Props.CONTAINER))

            # artifact collection
            self.collect = ProjectStepCollect(kwargs.get(Props.COLLECT))
            # artifact generation
            self.measure = ProjectStepMeasure(kwargs.get(Props.MEASURE))
        else:
            raise ValueError('kwargs must be dictionary')

        self.index = 0

    @property
    def ord_name(self):
        return '%02d-%s' % (self.index, self.name)

    def __repr__(self):
        return '{su}({self.ord_name})'.format(
            su=super(ProjectStage, self).__repr__(),
            self=self
        )

    @property
    def repeat(self):
        return self.smart_repeat.value
