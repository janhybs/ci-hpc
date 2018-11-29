#!/usr/bin/python
# author: Jan Hybs


import os
import copy
import time
import datetime
import cihpc.common.utils.strings

from cihpc.cfg.cfgutil import configure_string
from cihpc.core.structures.project_section import ProjectSection


class Counter(object):
    """
    Dummy class which simply counts on demand
    """

    def __init__(self, value=0):
        self.value = value

    @property
    def current(self):
        return self.current

    @property
    def next(self):
        self.value += 1
        return self.value - 1

    def __deepcopy__(self, memo):
        return Counter(self.value)

    def __getattr__(self, attr):
        prefix = 'next-'
        if attr.startswith(prefix):
            fmt = attr[len(prefix):]
            return ('{:%s}' % fmt).format(self.next)


class EnvGetter(object):

    def __deepcopy__(self, memo):
        return self

    def __getattr__(self, attr):
        return os.environ.get(attr, None)


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
        self.init_shell = kwargs.get('init-shell', None)
        self._counter = Counter()
        self._os = EnvGetter()
        self._global_args = dict(
            __project__=dict(
                start=dict(
                    datetime=datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S'),
                    timestamp=int(time.time()),
                    random=cihpc.common.utils.strings.generate_random_key(6),
                ),
                current=dict(

                ),
                counter=self._counter,
            ),
            os=self._os,
        )
        self._global_args['$'] = self._global_args['os']

        self.workdir = os.path.abspath(
            configure_string(kwargs.get('workdir', '.'), self.global_args)
        )
        # sections
        self.install = ProjectSection('install', kwargs.get('install', []))
        self.test = ProjectSection('test', kwargs.get('test', []))

    def unique(self):
        import uuid

        return uuid.uuid4().hex

    def update_global_args(self, o):
        self._global_args.update(o)

    @property
    def pretty(self):
        lines = [
            'Project <{self.name}>'.format(self=self),
            '  - workdir: {self.workdir}'.format(self=self),
            '%s' % cihpc.common.utils.strings.pad_lines('- {self.install.pretty}'.format(self=self)),
            '%s' % cihpc.common.utils.strings.pad_lines('- {self.test.pretty}'.format(self=self)),
        ]
        return '\n'.join(lines)

    @property
    def global_args(self):
        cp = copy.deepcopy(self._global_args)
        cp['__project__']['counter'] = self._counter  # restore counter
        cp['__project__']['current'] = dict(
            datetime=datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S'),
            timestamp=int(time.time()),
            random=cihpc.common.utils.strings.generate_random_key(6),
        )
        return cp

    @property
    def tmp_workdir(self):
        return os.path.join(self.workdir, 'tmp.%s' % self.name)

    def __repr__(self):
        return '<Project %s>' % self.name
