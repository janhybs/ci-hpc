#!/bin/python3
# author: Jan Hybs

import argparse
import collections
import locale
import logging
import os
import sys
import enum


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


class ArgAction(object):
    class Values(enum.Enum):
        RUN = 'run'
        FOREACH = 'foreach'

    def __init__(self, value):
        parts = str(value).split(':')
        self.enum = self.Values(parts[0])
        self.sections = parts[1:]

    def contains_stage(self, stage):
        return not self.sections or stage.name in self.sections

    def __repr__(self):
        return '{self.__class__.__name__}({self.enum}, {self.sections})'.format(self=self)


def parse_args(cmd_args=None):
    from cihpc.common.utils.parsing import RawFormatter

    # create parser
    parser = argparse.ArgumentParser(formatter_class=RawFormatter)
    parser.add_argument(
        '--git-url',
        default=None,
        help='''R|
        URL of the git repository. It has no usage for now but 
        it is planned in the future, where configuration may be
        part of the repository
    ''')
    parser.add_argument(
        '--git-commit', '--git-tag', '--commit',
        action='append',
        type=str,
        default=[],
        help='''R|
        SHA of the commit to work with.
        If no value is provided, will be checkout out to the
        last commit.
    ''')
    parser.add_argument(
        '--git-branch', '--branch',
        action='append',
        type=str,
        default=[],
        help='''R|
        Name of the branch to check out.
        If --git-commit is given, resulting git HEAD
        will be renamed to this value.
            This is useful when running commits from the past
            (there will be no detached state nor branch HEAD.)

        Default value is "master"
    ''')
    parser.add_argument(
        '-c', '--config-dir',
        type=str,
        default=None,
        help='''R|
        Path to the directory, where config.yaml (and optionally
        variables.yaml) file is/are located. If no value is set
        default value will current dir,
    ''')
    parser.add_argument(
        '--secret-yaml',
        type=str,
        default=None,
        help='''R|
        Path to the secret.yaml file which contains db config,
    ''')
    parser.add_argument(
        '--pbs',
        choices=['pbspro', 'pbs', 'local'],
        default=None, help='''R|
        If set, will generate bash file where it calls itself 
        once again, but without --execute flag.
    ''')
    parser.add_argument(
        '--execute',
        default=None, help='''R|
        Name of the script located in a config dir, which will be used 
        for in a qsub(bash) command
    ''')

    parser.add_argument(
        '--tty',
        default=False,
        action='store_true',
        help='''R|
        If set, will force tty human readable mode
    ''')

    parser.add_argument(
        'action',
        nargs='?',
        default='run',
        help='''R|
        Action to perform:
            - run (default) run the installation followed by the testing
            - git-foreach   will perform installation and testing 
                            for the previous commits in the main repository
                            See Git Foreach option group below for more details
        ''')

    # pbs options
    pbs_group_parser = parser.add_argument_group(
        'PBS options', 'other options applicable when in PBS mode'
    )
    pbs_group_parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=None,
        help='''R|
            If --execute is pbs (or any value besides local) will wait for the job to finish.
            By default there is no timeout. Specify in seconds.
        ''')
    pbs_group_parser.add_argument(
        '--check-interval',
        type=int,
        default=None,
        help='''R|
            If --execute is pbs (or any value besides local) will wait for the job to finish.
            Interval, in which the script queries the HPC for the job status.
            Specify in seconds.
        ''')

    gitlog_group_parser = parser.add_argument_group(
        'Git Foreach option',
        'when action is git-foreach, further specify what commits to choose and more')
    gitlog_group_parser.add_argument(
        '--watch-commit-limit',
        type=int,
        default=None,
        help='''R|
            When in 'watch' mode, represents number of commits to load
            from git log. Bigger number can cause git log to take longer.
            Smaller number may cause lower resolution, not catching
            all the changes made.
        ''')
    gitlog_group_parser.add_argument(
        '--watch-commit-policy', choices=['every-commit', 'commit-per-day'],
        default=None, help='''R|
            When in 'watch' mode, represents number of commits to load
            from git log. Bigger number can cause git log to take longer.
            Smaller number may cause lower resolution, not catching
            all the changes made.
        ''')

    # logging group

    log_group_parser = parser.add_argument_group(
        'Logging option',
        'further specify log level and log location.'
    )
    log_group_parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='''R|
        If set, will set log level to debug
    ''')
    log_group_parser.add_argument(
        '--log-path',
        type=str,
        default=None,
        help='''R|
        If set, will override standard log file location
    ''')
    # log_group_parser.add_argument(
    #     '--log-style',
    #     choices=['short', 'long'],
    #     default='short',
    #     help='''R|
    #     Format style of the logger
    # ''')
    log_group_parser.add_argument(
        '--log-level', '--log',
        default='info',
        choices=['debug', 'info', 'warning', 'error'],
        dest='log_level',
        help='''R|
            Level of the logger, available options are:
               - debug, info, warning, error
        ''')

    # parse given arguments
    args = parser.parse_args(cmd_args)

    # convert some fields
    args.action = ArgAction(args.action)
    args.log_level = getattr(logging, args.log_level.upper())
    if args.debug:
        args.log_level = logging.DEBUG
    return args


def _git_foreach(args, project):
    """

    Parameters
    ----------
    args: Namespace

    project: cihpc.core.processing.project.ProcessProject

    Returns
    -------

    """
    import logging

    from cihpc.cfg.config import global_configuration
    from cihpc.common.utils.git import Git
    from cihpc.git_tools import CommitHistoryExecutor
    from cihpc.git_tools.utils import ArgConstructor, CommitBrowser
    from cihpc.common.utils.parsing import convert_project_arguments
    from cihpc.core.processing.step_git import configure_git

    logger = logging.getLogger(__name__)

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


def main(cmd_args=None):
    from cihpc.common.logging import basic_config
    from cihpc.cfg.config import global_configuration
    import cihpc.cfg.cfgutil as cfgutil

    from cihpc.common.utils.parsing import defaultdict_type
    from cihpc.common.utils import strings as strings_utils

    from cihpc.core.processing.project import ProcessProject
    from cihpc.core.structures.project import Project
    from cihpc.core.execution import SeparateExecutor, ExecutionFactor

    # parse args
    args = parse_args(cmd_args)

    # configure the logging
    basic_config(
        level=args.log_level,
        log_path=args.log_path,
        stream=sys.stdout,
        stream_level=args.log_level,
        file_level=logging.DEBUG,
    )

    logger = logging.getLogger(__name__)

    # force tty mode if set
    if args.tty:
        global_configuration.tty = True

    if args.secret_yaml:
        global_configuration.cfg_secret_path = args.secret_yaml

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

    if args.action.enum is ArgAction.Values.FOREACH:
        project = _init_first_project(args, config_path, variables, project_name, project_dir)
        _git_foreach(args, project)
        sys.exit(0)

    # execute on demand using pbs/local or other system
    if args.pbs:
        script_content = SeparateExecutor.get_script(
            args, os.path.join(project_dir, args.execute or 'execute.sh')
        )

        executor = ExecutionFactor.create(
            args.pbs,
            script_content
        )
        logger.debug(executor)
        executor.submit()

        if args.timeout:
            result = executor.wait(args.timeout, kill=True)
            if result:
                sys.exit(0)
            else:
                sys.exit(1)
        sys.exit(0)

    # -----------------------------------------------------------------

    # otherwise load configs
    project_configs = cfgutil.configure_file(config_path, variables)
    for project_config in project_configs:
        # clear the cache
        from cihpc.artifacts.modules import CIHPCReportGit, CIHPCReport

        CIHPCReport.inited = False
        CIHPCReportGit.instances = dict()

        logger.debug('yaml configuration: \n%s', strings_utils.to_yaml(project_config))

        # specify some useful global arguments which will be available in the config file
        global_args_extra = {
            'project-name': project_name,
            'project-dir' : project_dir,
            'arg'         : dict(
                branch=collections.defaultdict(lambda: 'master', **dict(args.git_branch)),
                commit=collections.defaultdict(lambda: '', **dict(args.git_commit)),
            )
        }

        # parse config
        project_definition = Project(project_name, **project_config)
        project_definition.update_global_args(global_args_extra)

        # prepare process
        project = ProcessProject(project_definition)
        logger.info('processing project %s, action %s', project_name, args.action)

        if args.action.enum is ArgAction.Values.RUN:
            for stage in project_definition.stages:
                if stage and args.action.contains_stage(stage):
                    project.process_stage(stage)


def _init_first_project(args, config_path, variables, project_name, project_dir):
    from cihpc.cfg import cfgutil
    from cihpc.core.processing.project import ProcessProject
    from cihpc.core.structures.project import Project

    project_configs = cfgutil.configure_file(config_path, variables)
    for project_config in project_configs:
        # specify some useful global arguments which will be available in the config file
        global_args_extra = {
            'project-name': project_name,
            'project-dir' : project_dir,
            'arg'         : dict(
                branch=collections.defaultdict(lambda: 'master', **dict(args.git_branch)),
                commit=collections.defaultdict(lambda: '', **dict(args.git_commit)),
            )
        }

        # parse config
        project_definition = Project(project_name, **project_config)
        project_definition.update_global_args(global_args_extra)

        # prepare process
        return ProcessProject(project_definition)
