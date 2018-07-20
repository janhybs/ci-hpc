#!/usr/bin/python
# author: Jan Hybs


import os
import copy
import time
import datetime
import utils.strings

from structures.project_section import ProjectSection


class Project(object):
    """
    Main class representing single project in a yaml configuration file
    :type test:        ProjectSection
    :type install:     ProjectSection
    :type init_shell:  str
    :type workdir:     str
    :type name:        str
    """

    def __init__(self, name, **kwargs):

        # globals
        self.name = name
        self.workdir = os.path.abspath(kwargs.get('workdir', '.'))
        self.init_shell = kwargs.get('init-shell', None)
        self._global_args = dict(
            __project__=dict(
                start=dict(
                    datetime=datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S'),
                    timestamp=int(time.time()),
                    random=utils.strings.generate_random_key(6),
                ),
                current=dict(

                )

            )
        )

        # sections
        self.install = ProjectSection('install', kwargs.get('install', []))
        self.test = ProjectSection('test', kwargs.get('test', []))

    @property
    def global_args(self):
        cp = copy.deepcopy(self._global_args)
        cp['__project__']['current'] = dict(
            datetime=datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S'),
            timestamp=int(time.time()),
            random=utils.strings.generate_random_key(6),
        )
        return cp

    def __repr__(self):
        return '<Project %s>' % self.name