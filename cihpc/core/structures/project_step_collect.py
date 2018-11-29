#!/usr/bin/python
# author: Jan Hybs


import cihpc.core.structures
from cihpc.core.structures.project_step_collect_parse import ProjectStepContainerParse


class ProjectStepCollect(object):
    """
    Class definition for artifact collection
    :type files:        str
    :type parse:        ProjectStepContainerParse
    :type module:       str
    :type move_to:      str
    :type cut_prefix:   str
    :type extra:        dict
    :type repo:         str
    :type type:         str
    :type save_to_db:   bool
    """

    def __init__(self, **kwargs):
        self.files = kwargs.get('files', None)
        self.parse = cihpc.core.structures.new(kwargs, 'parse', ProjectStepContainerParse)
        self.module = kwargs.get('module', 'cihpc.artifacts.collect.modules.generic_module')
        self.move_to = kwargs.get('move-to', None)
        self.cut_prefix = kwargs.get('cut-prefix', None)
        self.extra = kwargs.get('extra', dict())
        self.repo = kwargs.get('repo', None)
        self.save_to_db = kwargs.get('save-to-db', True)
        self.type = kwargs.get('type', 'json')
