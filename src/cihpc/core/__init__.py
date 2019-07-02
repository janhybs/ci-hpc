#!/bin/python3
# author: Jan Hybs

import argparse
import collections
import locale
from loguru import logger
import os
import sys


logger.level('DURATION', no=38, color='<Y><bold><r>')
# logger.configure(handlers=[])
from cihpc.core.parsers import ArgAction, parse_args


if locale.getpreferredencoding().upper() not in ('UTF8', 'UTF-8'):
    locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')

if str(getattr(sys.stdout, 'encoding', '')).upper() not in ('UTF8', 'UTF-8'):
    print('stdout encoding is not UTF-8, you should prepand\n'
          'start command with:\n'
          '  PYTHONIOENCODING=utf-8 python3 <your-command-here>')
    try:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
    except:
        pass


def _git_foreach(args, project):
    """

    Parameters
    ----------
    args: Namespace

    project: cihpc.core.processing.project.ProcessProject

    Returns
    -------

    """
    from loguru import logger

    from cihpc.cfg.config import global_configuration
    from cihpc.common.utils.git import Git
    from cihpc.git_tools import CommitHistoryExecutor
    from cihpc.git_tools.utils import ArgConstructor, CommitBrowser
    from cihpc.common.utils.parsing import convert_project_arguments
    from cihpc.core.processing.step_git import configure_git

    if not global_configuration.project_git:
        logger.error('no repository provided')
        exit(0)

    project_commit_format = global_configuration.project_git.commit
    if not project_commit_format or not str(project_commit_format).strip():
        logger.error('project repository must be configurable via <arg.commit.foobar> placeholder')

    project_commit_format = str(project_commit_format).strip()
    if project_commit_format.startswith('<arg.commit.') and project_commit_format.endswith('>'):
        commit_field = project_commit_format[len('<arg.commit.'):-1]
        fixed_args = global_configuration.exec_args \
                     + convert_project_arguments(args, excludes=['action', 'config-dir'])

        fixed_args += ['--config-dir', global_configuration.project_cfg_dir]
        fixed_args += ['--secret-yaml', global_configuration.cfg_secret_path]
        fixed_args += [':'.join([ArgAction.Values.RUN.value] + args.action.sections)]

        args_constructor = ArgConstructor(fixed_args, commit_field)
        commit_browser = CommitBrowser(
            Git(configure_git(global_configuration.project_git, project.definition.global_args)),
            limit=args.watch_commit_limit,
            commit_policy=args.watch_commit_policy,
        )
        logger.info('analyzing last %d commits, commit pick policy: %s' % (
            commit_browser.limit, commit_browser.commit_policy))
        service = CommitHistoryExecutor(project.definition.name, args_constructor, commit_browser)

        service.run()


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
        logger.debug('determined config dir: %s' % project_dir)
        config_path = os.path.join(project_dir, 'config.yaml')

        global_configuration.project_cfg_dir = project_dir
        global_configuration.project_cfg = config_path

    # this file contains all the sections and actions for installation and testing
    config_yaml = cfgutil.yaml_load(cfgutil.read_file(config_path))
    project_name = config_yaml.get('project', None)

    if project_name is None:
        logger.error('configuration file\n%s\n'
                     'does not contain required field "project"' % config_path)
        logger.error(cfgutil.read_file(config_path))
        sys.exit(1)

    logger.info('running cihpc for the project %s' % project_name)
    logger.debug('app args: %s', str(args))

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

        logger.debug('yaml configuration: \n%s', strings_utils.to_yaml(project_config))

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


def main(cmd_args=None):
    from cihpc.cfg.config import global_configuration

    from cihpc.core.processing.project import ProcessProject
    from cihpc.core.structures.project import Project
    from cihpc.core.execution import SeparateExecutor, ExecutionFactor

    # parse args
    args = parse_args(cmd_args)

    # force tty mode if set
    if args.tty:
        global_configuration.tty = True

    if args.secret_yaml:
        global_configuration.cfg_secret_path = args.secret_yaml

    # -------------------------------------------------------

    for project_definition in iter_project_definition(args):
        # prepare process
        project = ProcessProject(project_definition)
        logger.info(f'processing project {project_definition.name}, action {args.action}')

        if args.action.enum is ArgAction.Values.RUN:
            for stage in project_definition.stages:
                if stage and args.action.contains_stage(stage):
                    project.process_stage(stage)


def _init_first_project(args, config_path, variables, project_name, project_dir):
    from cihpc.cfg import cfgutil
    from cihpc.cfg import config as env
    from cihpc.core.processing.project import ProcessProject
    from cihpc.core.structures.project import Project

    project_configs = cfgutil.configure_file(config_path, variables)
    for project_config in project_configs:
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
        project_definition = Project(project_name, global_args_extra, **project_config)

        # prepare process
        return ProcessProject(project_definition)


if __name__ == '__main__':
    main()
