#!/bin/python3
# author: Jan Hybs

import itertools
import logging
import os
from collections import namedtuple
from enum import Enum

import yaml

from cihpc.cfg.cfgutil import find_valid_configuration
from cihpc.cfg.config import global_configuration
from cihpc.common.utils import dateutils
from cihpc.common.utils.colors import configurable_html_color


logger = logging.getLogger(__name__)


sns_color_palette = [
    [
        0.12156862745098039,
        0.4666666666666667,
        0.7058823529411765
    ],
    [
        1.0,
        0.4980392156862745,
        0.054901960784313725
    ],
    [
        0.17254901960784313,
        0.6274509803921569,
        0.17254901960784313
    ],
    [
        0.8392156862745098,
        0.15294117647058825,
        0.1568627450980392
    ],
    [
        0.5803921568627451,
        0.403921568627451,
        0.7411764705882353
    ],
    [
        0.5490196078431373,
        0.33725490196078434,
        0.29411764705882354
    ],
    [
        0.8901960784313725,
        0.4666666666666667,
        0.7607843137254902
    ],
    [
        0.4980392156862745,
        0.4980392156862745,
        0.4980392156862745
    ],
    [
        0.7372549019607844,
        0.7411764705882353,
        0.13333333333333333
    ],
    [
        0.09019607843137255,
        0.7450980392156863,
        0.8117647058823529
    ]
]


class ProjectConfig(object):
    _instances = dict()

    @classmethod
    def get(cls, project_name):
        """
        Parameters
        ----------
        project_name : str
            a name of the project

        Returns
        -------
        cihpc.www.cfg.project_config.ProjectConfig
            A instance of ProjectConfig for the given project

        """
        if project_name not in cls._instances or True:
            cls._instances[project_name] = ProjectConfig(
                cls._get_project_config(
                    project_name
                )
            )
        return cls._instances[project_name]

    @staticmethod
    def _get_project_config(project_name):

        cfg_dir = find_valid_configuration(
            os.path.join(global_configuration.cfg, project_name),
            os.path.join(global_configuration.cwd, project_name),
            os.path.join(global_configuration.cwd, 'cfg', project_name),
            file='www.yaml'
        )
        if not cfg_dir:
            logger.error('no valid configuration found for the project %s\n'
                         ' the paths that were tried: \n   %s', project_name,
                         '\n   '.join([
                             '<cfg>/<project>   ' + os.path.join(global_configuration.cfg, project_name),
                             './cfg/<project>   ' + os.path.join(global_configuration.cwd, project_name),
                             './<project>       ' + os.path.join(global_configuration.cwd, 'cfg', project_name)
                         ]))
            exit(1)

        cfg_path = os.path.join(cfg_dir, 'www.yaml')

        with open(cfg_path, 'r') as fp:
            return yaml.load(fp)

    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
            Yaml configuration taken from www/cfg/<project-name>.yaml file
        """
        self.cfg = config
        self.name = config.get('name')
        self.desc = config.get('desc', None)

        self.test_view = ProjectConfigTestView(config.get('test-view', {}))
        self.scale_view = ProjectConfigScaleView(config.get('scale-view', {}))
        self.frame_view = ProjectConfigFrameView(config.get('frame-view', {}))
        self.tests = [ProjectConfigTest(x) for x in config.get('tests', [])]

        self.date_format = None
        self.color_palette = [configurable_html_color([int(y * 255) for y in x]) for x in sns_color_palette.copy()]

        date_format = config.get('date-format', 'long')
        if date_format == 'long':
            self.date_format = dateutils.long_format
        elif date_format == 'short':
            self.date_format = dateutils.short_format

        self.fields = ProjectConfigFields(config.get('fields', {}))

    def get_test_view_groupby(self):
        """
        a method will generate section for grouping and renaming when
        processing test view

        Returns
        -------
        tuple[dict, dict]

        """
        agg = dict()
        agg.update(({
            self.test_view.git_hash_prop: 'first',
            self.test_view.id_prop      : 'first',
        }))
        renames = dict()
        renames.update(({
            self.test_view.git_hash_prop: 'commit',
            self.test_view.id_prop      : 'id',
        }))

        for extra in self.test_view.extra.vars:
            agg[extra.map_from] = extra.map_via
            if extra.map_from != extra.map_to:
                renames[extra.map_from] = extra.map_to

        return agg, renames


class ProjectConfigView(object):
    MATCH_ALL = '*'

    def get_projection(self):
        get_projection_list = getattr(self, 'get_projection_list', None)
        if get_projection_list:
            return dict(zip(get_projection_list(), itertools.repeat(1)))
        else:
            return dict()


class ViewMode(Enum):
    TIME_SERIES = 'time-series'
    SCALE_VIEW = 'scale-view'


class FieldExpression(object):
    _operators = list('+-*/')

    def __init__(self, conf, name):
        self.name = name
        self.expression = conf.get(self.name, None)

        if not self.expression:
            self.is_complex = False
            self.fields = set()
            self.func = lambda row: None
            self.valid = False
            return

        self.fields = set()
        self.valid = True

        if self.expression.startswith('='):
            self.is_complex = True
            self.func = eval('lambda row: ' + self.expression[1:])
        else:
            self.is_complex = False
            self.func = lambda row: row[self.expression]
            self.fields.add(self.expression)

    def __bool__(self):
        return self.valid

    def __repr__(self):
        return '<%s>' % self.name


class ProjectConfigFields(object):
    _result = namedtuple('Result', ['duration', 'returncode'])
    _git = namedtuple('Git', ['datetime', 'commit', 'branch'])
    _problem = namedtuple('Problem', ['test', 'case', 'subcase', 'cpu', 'size', 'per_cpu', 'scale'])

    def __init__(self, fields: dict):
        self.result = self._result(
            FieldExpression(fields, 'result.duration'),
            FieldExpression(fields, 'result.returncode'),
        )
        self.git = self._git(
            FieldExpression(fields, 'git.datetime'),
            FieldExpression(fields, 'git.commit'),
            FieldExpression(fields, 'git.branch'),
        )
        self.problem = self._problem(
            FieldExpression(fields, 'problem.test'),
            FieldExpression(fields, 'problem.case'),
            FieldExpression(fields, 'problem.subcase'),
            FieldExpression(fields, 'problem.cpu'),
            FieldExpression(fields, 'problem.size'),
            FieldExpression(fields, 'problem.per.cpu'),
            FieldExpression(fields, 'problem.scale'),
        )
        self.extra = fields.get('extra', list())

    def required_fields(self):
        result = set()
        for i in [self.result, self.git, self.problem]:
            for j in i:
                result |= j.fields
        result |= set(self.extra)

        return result

    def apply_to_df(self, df):
        for field_group in [self.result, self.git, self.problem]:
            for field in field_group:
                if field:
                    df[field.name] = df.apply(field.func, axis=1)
        return df

    def __repr__(self):
        return str(self.__dict__)


class ProjectConfigScaleView(ProjectConfigView):
    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
            a piece of configuration for the view
        """
        self.groupby = config.get('groupby', dict())
        self.series = config.get('series', list())

        self.x_prop = config.get('x-property', 'git.datetime')
        self.y_prop = config.get('y-property', 'result.duration')
        self.c_prop = config.get('cpu-property', 'problem.cpus')
        self.s_prop = config.get('size-property', 'problem.size')

        self.git_hash_prop = config.get('commit-property', 'git.commit')
        self.id_prop = config.get('id-property', '_id')

    def get_filters(self, values):
        """
        Parameters
        ----------
        values : dict
            a key value dictionary where key is name of the filter
            and value is value of the filter, * means everything
            and thus will not create any filter
        """
        result = dict()

        for group_name, group_field in self.groupby.items():
            if group_field is None:
                continue

            if group_name in values:
                value = values[group_name]
                if value not in (None, self.MATCH_ALL, ""):
                    result[group_field] = values[group_name]

        for f_name, f_value in values.items():
            if f_value not in (None, self.MATCH_ALL, ""):
                result[f_name] = f_value

        return result

    def get_projection_list(self):
        result = list()
        result.extend([
            '_id',
            self.x_prop,
            self.y_prop,
            self.c_prop,
            self.id_prop,
            self.git_hash_prop,
        ])
        result.extend(self.groupby.values())
        result.extend([k for s in self.series for k in s.get('filters', {})])
        return [x for x in result if x is not None]


class ProjectConfigTestView(object):
    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
            a piece of configuration for the view
        """
        self.groupby = config.get('groupby', dict())


class ProjectConfigFrameView(ProjectConfigView):
    _fields = namedtuple('Field', ['timers'])
    _timers = namedtuple('Timer', ['duration', 'name', 'path'])

    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
            a piece of configuration for the view
        """
        self.groupby = config.get('groupby', {})

        self.unwind = config.get('unwind', 'timers')
        fields = config.get('fields', {})
        self.fields = self._fields(
            self._timers(
                FieldExpression(fields, 'timers.duration'),
                FieldExpression(fields, 'timers.name'),
                FieldExpression(fields, 'timers.path'),
            )
        )


class ProjectConfigTest(object):
    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
            a test configuration piece
        """
        self.name = config.get('name')
        self.desc = config.get('desc', None)
        self.tests = [ProjectConfigTest(x) for x in config.get('tests', [])]


class ProjectConfigViewExtra(object):
    """
    Attributes
    ----------
    vars : list[bool]
        a list of extra variables
    """

    def __init__(self, config):
        """
        Parameters
        ----------
        config : list[str|dict]
            a list of extra variables to register
        """
        self.vars = list()
        for v in config:
            if isinstance(v, str):
                self.vars.append(
                    ProjectConfigViewExtraVariable(
                        map_from=v,
                        map_to=v,
                        map_via='first'
                    )
                )
            elif isinstance(v, dict):
                self.vars.append(
                    ProjectConfigViewExtraVariable(
                        map_from=v.get('from'),
                        map_to=v.get('to', v.get('from')),
                        map_via=v.get('via', 'first')
                    )
                )


class ProjectConfigViewExtraVariable(object):
    def __init__(self, map_from, map_to, map_via='first'):
        self.map_from = map_from
        self.map_to = map_to

        if map_via == 'first':
            self.map_via = map_via
        elif map_via == 'push':
            self.map_via = lambda x: list(x)
        else:
            import numpy as np

            self.map_via = getattr(np, map_via)
