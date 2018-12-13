#!/usr/bin/python
# author: Jan Hybs
import enum

from cihpc.core.structures.a_project import ComplexClass


class ProjectStepMeasure(ComplexClass):
    """
    Class definition for automatic artifact measuring. The process may not be precise
    as what is measured is entire execution of the shell script

    :type format:       str
    :type type:         ProjectStepMeasure.Type
    :type move_to:      str
    """

    class Type(enum.Enum):
        TYPE_INSTRUMENT_SHELL = 'instrument-shell'
        TYPE_MEASURE_SCRIPT = 'measure-script'

    def __init__(self, kwargs):
        super(ProjectStepMeasure, self).__init__(kwargs)
        if not self:
            return

        if isinstance(kwargs, dict):
            self.format = kwargs.get('format', 'json')
            self.type = self.Type(kwargs.get('type', self.Type.TYPE_INSTRUMENT_SHELL.value))
            self.move_to = kwargs.get('move-to', '.')
        else:
            raise ValueError('kwargs must be dict')
