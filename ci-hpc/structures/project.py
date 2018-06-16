#!/usr/bin/python
# author: Jan Hybs


import os

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
        self.global_args = dict()

        # sections
        self.install = ProjectSection('install', kwargs.get('install', []))
        self.test = ProjectSection('test', kwargs.get('test', []))

    def __repr__(self):
        return '<Project %s>' % self.name