#!/bin/python3
# author: Jan Hybs

import os

import itertools
import yaml

from utils import dateutils
from utils.colors import configurable_html_color
from utils.glob import global_configuration
from utils.logging import logger


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
        visualisation.www.plot.cfg.project_config.ProjectConfig
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
        cfg_path = os.path.join(
            global_configuration.root,
            'www', 'cfg', '%s.yaml' % project_name
        )

        if not os.path.exists(cfg_path):
            logger.error(
                'No valid project configuration found for the project %s. \n'
                'at location %s \n',
                project_name,
                cfg_path
            )
            exit(1)

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
        self.frame_view = ProjectConfigFrameView(config.get('frame-view', {}))
        self.tests = [ProjectConfigTest(x) for x in config.get('tests', [])]

        self.date_format = None
        self.color_palette = [configurable_html_color([int(y*255) for y in x]) for x in sns_color_palette.copy()]

        date_format = config.get('date-format', 'long')
        if date_format == 'long':
            self.date_format = dateutils.long_format
        elif date_format == 'short':
            self.date_format = dateutils.short_format

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
            self.test_view.id_prop: 'first',
        }))
        renames = dict()
        renames.update(({
            self.test_view.git_hash_prop: 'commit',
            self.test_view.id_prop: 'id',
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


class ProjectConfigTestView(ProjectConfigView):
    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
            a piece of configuration for the view
        """
        self.groupby = config.get('groupby', {
            'test-name': 'problem.test-name',
            'case-name': 'problem.case-name',
        })

        self.colorby = config.get('colorby', {
            'case-cpus': 'problem.cpus',
            'case-size': 'problem.case-size',
        })

        self.unwind = config.get('unwind', {
            'from': 'timers',
            'to':   'timer',
        })

        self.x_prop = config.get('x-property', 'git.datetime')
        self.y_prop = config.get('y-property', 'result.duration')

        self.git_hash_prop = config.get('commit-property', 'git.commit')
        self.id_prop = config.get('id-property', '_id')

        self.extra = ProjectConfigViewExtra(config.get('extra', []))
        self.smooth = config.get('smooth', False)
        self.uniform = config.get('uniform', True)

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
                if value not in (None, self.MATCH_ALL):
                    result[group_field] = values[group_name]

        return result

    def get_projection_list(self):
        result = list()
        result.extend([
            '_id',
            self.x_prop,
            self.y_prop,
            self.id_prop,
            self.git_hash_prop,
        ])
        result.extend(self.groupby.values())
        result.extend(self.colorby.values())
        result.extend([x.map_from for x in self.extra.vars])
        return result


class ProjectConfigFrameView(ProjectConfigView):
    def __init__(self, config):
        """
        Parameters
        ----------
        config : dict
            a piece of configuration for the view
        """
        self.groupby = config.get('groupby', {
            'git-datetime': 'git.datetime',
            'case-cpus': 'problem.cpus',
        })

        self.unwind = config.get('unwind', {
            'from': 'timers',
            'to':   'timer',
        })

        self.x_prop = config.get('x-property', 'timer.name')
        self.y_prop = config.get('y-property', 'timer.duration')

        self.id_prop = config.get('id-property', '_id')

    def get_projection_list(self):
        result = list()
        result.extend([
            '_id',
            self.unwind['from'],
            self.x_prop,
            self.y_prop,
            self.id_prop,
        ])
        result.extend(self.groupby.values())
        return result


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


