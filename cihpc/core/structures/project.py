#!/usr/bin/python
# author: Jan Hybs


import os
import copy
import time
import datetime as dt
import cihpc.common.utils.strings as strings

from cihpc.cfg.cfgutil import configure_string
from cihpc.core.structures.project_section import ProjectSection
from cihpc.core.structures.project_stage import ProjectStages


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

    def __repr__(self):
        return 'CNT({self.value})'.format(
            self=self
        )


class EnvGetter(object):

    def __deepcopy__(self, memo):
        return self

    def __getattr__(self, attr):
        return os.environ.get(attr, None)

    def __repr__(self):
        return '<ENV>'


class DatePoint(object):
    def __init__(self, datetime=None, timestamp=None, random=None):
        if not datetime:
            datetime = dt.datetime.now()

        self._datetime = datetime
        self.datetime = datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
        self.date = datetime.now().strftime('%Y_%m_%d')
        self.time = datetime.now().strftime('%H_%M_%S')
        self.timestamp = timestamp or int(time.time())
        self.random = random or strings.generate_random_key(6)

    def __getattr__(self, attr):
        return self.__dict__.get(attr)

    def __deepcopy__(self, memo):
        return DatePoint(self._datetime, self.timestamp, self.random)

    def __repr__(self):
        return '<DatePoint>'


class Project(object):
    """
    Main class representing single project in a yaml configuration file
    :type test:        ProjectSection
    :type install:     ProjectSection
    :type stages:      list[cihpc.core.structures.project_stage.ProjectStage]
    :type init_shell:  str
    :type workdir:     str
    :type name:        str
    """

    def __init__(self, name, **kwargs):
        # globals
        self.name = name
        self.init_shell = kwargs.get('init-shell', None)
        self.use_database = not kwargs.get('no-database', False)

        self._secure_name = strings.secure_filename(self.name)
        self._counter = Counter()
        self._os = EnvGetter()
        self._global_args = dict(
            __project__=dict(
                start=DatePoint(),
                current=DatePoint(),
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

        # stages
        self.stages = ProjectStages(kwargs.get('stages'))

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
            '%s' % strings.pad_lines('- {self.install.pretty}'.format(self=self)),
            '%s' % strings.pad_lines('- {self.test.pretty}'.format(self=self)),
        ]
        return '\n'.join(lines)

    @property
    def global_args(self):
        cp = copy.deepcopy(self._global_args)
        cp['__project__']['counter'] = self._counter  # restore counter
        cp['__project__']['current'] = DatePoint()
        return cp

    @property
    def tmp_workdir(self):
        return os.path.join(self.workdir, 'tmp.%s' % self._secure_name)

    def __repr__(self):
        return '<Project %s>' % self._secure_name
