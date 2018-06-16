#!/usr/bin/python
# author: Jan Hybs


class ProjectStepCollect(object):
    """
    :type files:        str
    :type module:       str
    :type move_to:      str
    :type cut_prefix:   str
    :type extra:        dict
    """
    def __init__(self, **kwargs):
        self.files = kwargs.get('files', '.')
        self.module = kwargs.get('module', 'Flow123dProfiler')
        self.move_to = kwargs.get('move-to', None)
        self.cut_prefix = kwargs.get('cut-prefix', None)
        self.extra = kwargs.get('extra', dict())