#!/usr/bin/python
# author: Jan Hybs


from cihpc.common.utils.parallels import determine_cpus


class ProjectStepParallel(object):
    """
    A class containing information about parallel mode
    :type cpus: int
    :type prop: any
    """

    def __init__(self, kwargs=False):
        if not kwargs or kwargs in (None, False):
            kwargs = dict()

        if kwargs is True:
            kwargs = dict(cpus='100%', prop=1)

        self.enabled = bool(kwargs)
        self.prop = kwargs.get('prop', None)
        self.cpus = determine_cpus(
            kwargs.get('cpus', 1)
        )

    def __bool__(self):
        return self.enabled
