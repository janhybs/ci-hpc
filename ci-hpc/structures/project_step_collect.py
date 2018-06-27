#!/usr/bin/python
# author: Jan Hybs


class ProjectStepCollect(object):
    """
    Class definition for artifact collection
    :type files:        str
    :type module:       str
    :type move_to:      str
    :type cut_prefix:   str
    :type extra:        dict
    :type repo:         str
    :type save_to_db:   bool
    """
    def __init__(self, **kwargs):
        self.files = kwargs.get('files', '.')
        self.module = kwargs.get('module', 'Flow123dProfiler')
        self.move_to = kwargs.get('move-to', None)
        self.cut_prefix = kwargs.get('cut-prefix', None)
        self.extra = kwargs.get('extra', dict())
        self.repo = kwargs.get('repo', None)
        self.save_to_db = kwargs.get('save_to_db', True)