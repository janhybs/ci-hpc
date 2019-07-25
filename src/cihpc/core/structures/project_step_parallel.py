#!/usr/bin/python
# author: Jan Hybs

from loguru import logger


from cihpc.common.utils.parallels import determine_cpus
from cihpc.core.structures.a_project import ComplexClass


class ProjectStepParallel(ComplexClass):
    """
    A class containing information about parallel mode
    :type cpus: int
    :type prop: any
    """

    def __init__(self, kwargs=False):
        super(ProjectStepParallel, self).__init__(kwargs)

        if not kwargs or kwargs in (None, False):
            self.cpus = 1
            self.prop = None

        elif kwargs is True:
            self.cpus = determine_cpus('51%')
            self.prop = None
        elif isinstance(kwargs, dict):
            try:
                self.cpus = determine_cpus(kwargs.get('cpus', 1))
                self.prop = kwargs.get('prop', None)
            except ValueError as e:
                logger.warning(f'error while determining cpus value, will use 1 core\n'
                               f'{e}')
                self.cpus = 1
                self.prop = None
                self._enabled = False
        else:
            raise ValueError('ProjectStepParallel: expected None, bool or dict')

    def __repr__(self):
        return 'Parallel(cpus={self.cpus}, prop={self.prop})'.format(
            self=self
        )
