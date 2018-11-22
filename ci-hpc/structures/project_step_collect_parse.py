#!/usr/bin/python
# author: Jan Hybs


class ProjectStepContainerParse(object):
    """
    Helper class which holds information about singularity/docker
    """

    def __init__(self, **kwargs):
        """
        Parameters
        ----------
        kwargs : dict
            settings for the parser
        """

        self.type = kwargs.get('type', 'json')
        self.start = kwargs.get('start', None)
        self.stop = kwargs.get('start', None)
