#!/bin/python3
# author: Jan Hybs

import collections
import locale
from loguru import logger
import sys

from cihpc.core.utils import iter_project_definition


logger.level('DURATION', no=38, color='<Y><bold><r>')
# logger.configure(handlers=[])
from cihpc.core.parsers.run_parser import ArgAction, parse_args


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
        logger.info(f'analyzing last {commit_browser.limit} commits, commit pick policy: {commit_browser.commit_policy}')
        service = CommitHistoryExecutor(project.definition.name, args_constructor, commit_browser)

        service.run()


def main(cmd_args=None):
    from cihpc.cfg.config import global_configuration

    from cihpc.core.processing.project import ProcessProject
    from cihpc.core.structures.project import Project

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
