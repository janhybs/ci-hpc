#!/usr/bin/python
# author: Jan Hybs


import os

from cihpc.core.structures.a_project import ComplexClass


class ProjectStepContainer(ComplexClass):
    """
    Helper class which holds information about singularity/docker
    """

    def __init__(self, kwargs):
        """
        Parameters
        ----------
        value : str
            lines to load container module and to exec singularity/docker
        """
        super(ProjectStepContainer, self).__init__(kwargs)
        self.exec = self._parse_exec_value(kwargs) if self else None

    @staticmethod
    def _parse_exec_value(value):
        """
        Parameters
        ----------
        value : str
            lines to load container module and to exec singularity/docker
        """
        if value.find('%s') != -1:
            return value
        else:

            # the given value does not contain substitute placeholder
            # we need to determine what format was given
            if value.find('docker run') != -1:
                # assuming user forget about substitution
                return value.strip() + ' %s'
            elif value.find('.simg'):
                # a singularity image was maybe given?
                filepath = value.strip()
                if os.path.exists(filepath):
                    return 'singularity exec %s %%s' % filepath
                else:
                    # file does not exists so assume it was a name of a docker image
                    pass

        # we assume the docker image name was given
        return 'docker run --rm -v $(pwd):$(pwd) -w $(pwd) %s %%s' % value.strip()

    def __repr__(self):
        return '{self._enable_str}Container({self.exec})'.format(
            self=self
        )
