#!/bin/python3
# author: Jan Hybs
import argparse
import collections
import os
import sys
from collections import __init__

from loguru import logger


def iter_project_definition(args: argparse.Namespace = None):
    from cihpc.cfg.config import global_configuration
    import cihpc.cfg.cfgutil as cfgutil
    from cihpc.cfg import config as env

    from cihpc.common.utils.parsing import defaultdict_type
    from cihpc.common.utils import strings as strings_utils

    from cihpc.core.processing.project import ProcessProject
    from cihpc.core.structures.project import Project
    from cihpc.core.execution import SeparateExecutor, ExecutionFactor

    # -------------------------------------------------------

    # all configuration files are cfg/<project-name> directory if not set otherwise
    project_dir = cfgutil.find_valid_configuration(
        args.config_dir,
        global_configuration.home,
        file='config.yaml',
        raise_if_not_found=True
    )

    if not project_dir:
        logger.error('termination execution')
        sys.exit(1)
    else:
        logger.debug(f'determined config dir: {project_dir}')
        config_path = os.path.join(project_dir, 'config.yaml')

        global_configuration.project_cfg_dir = project_dir
        global_configuration.project_cfg = config_path

    # this file contains all the sections and actions for installation and testing
    config_yaml = cfgutil.yaml_load(cfgutil.read_file(config_path))
    project_name = config_yaml.get('project', None)

    if project_name is None:
        logger.error(f'configuration file\n{config_path}\n'
                     f'does not contain required field "project"')
        logger.error(cfgutil.read_file(config_path))
        sys.exit(1)

    logger.info(f'running cihpc for the project {project_name}')
    logger.debug(f'app args: {str(args)}')

    # convert list ["key:value", "key2:value2", ...] to dict {key:value, key2:value2}
    # default value for this dictionary is string value 'master'
    args.git_branch = defaultdict_type(args.git_branch, 'master', project_name)

    # default value for this dictionary is string value ''
    args.git_commit = defaultdict_type(args.git_commit, '', project_name)

    # this file contains only variables which can be used in config.yaml
    variables_path = os.path.join(project_dir, 'variables.yaml')

    # update cpu count
    variables = cfgutil.load_config(variables_path)
    # variables['cpu-count'] = args.cpu_count

    global_configuration.project_name = project_name

    # -----------------------------------------------------------------

    # otherwise load configs
    project_configs = cfgutil.configure_file(config_path, variables)
    for project_config in project_configs:
        # clear the cache
        # from cihpc.artifacts.modules import CIHPCReportGit, CIHPCReport
        #k
        # CIHPCReport.inited = False
        # CIHPCReportGit.instances = dict()

        logger.debug(f'yaml configuration: \n%s' % strings_utils.to_yaml(project_config))

        # specify some useful global arguments which will be available in the config file
        global_args_extra = {
            'tmp'         : env.__tmp__,
            'project-name': project_name,
            'project-dir' : project_dir,
            'arg'         : dict(
                branch=collections.defaultdict(lambda: 'master', **dict(args.git_branch)),
                commit=collections.defaultdict(lambda: '', **dict(args.git_commit)),
            )
        }

        # parse config
        yield Project(project_name, global_args_extra, **project_config)
