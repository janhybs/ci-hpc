#!/bin/python3
# author: Jan Hybs

import argparse
import collections
import locale
import logging
import os
import sys


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


def parse_args(cmd_args=None):
    from cihpc.common.utils.parsing import RawFormatter

    # create parser
    parser = argparse.ArgumentParser(formatter_class=RawFormatter)
    parser.add_argument('-p', '--project', type=str, required=True, help='''R|
                            Name of the project.
                            Based on this value, proper configuration will be
                            loaded (assuming --config-dir) was not set.
                            ''')
    parser.add_argument('--git-url', type=str, default=None, help='''R|
                            URL of the git repository. It has no usage for now but 
                            it is planned in the future, where configuration may be
                            part of the repository
                            ''')
    parser.add_argument('--git-commit', action='append', type=str, default=[], help='''R|
                            SHA of the commit to work with.
                            If no value is provided, will be checkout out to the
                            last commit.
                            ''')
    parser.add_argument('--git-branch', action='append', type=str, default=[], help='''R|
                            Name of the branch to check out.
                            If --git-commit is given, resulting git HEAD
                            will be renamed to this value.
                                This is useful when running commits from the past
                                (there will be no detached state nor branch HEAD.)

                            Default value is "master" ''')
    parser.add_argument('-c', '--config-dir', type=str, default=None, help='''R|
                            Path to the directory, where config.yaml (and optionally
                            variables.yaml) file is/are located. If no value is set
                            default value will cfg/<project>,
                            where <project> is name of the project given.
                            ''')
    parser.add_argument('--pbs', choices=['pbspro', 'pbs', 'local'], default=None, help='''R|
                            If set, will generate bash file where it calls itself 
                            once again, but without --execute flag.
                            ''')
    parser.add_argument('--timeout', '-t', type=int, default=None, help='''R|
                            If --execute is pbs (or any value besides local) will wait for the job to finish.
                            By default there is no timeout. Specify in seconds.
                            ''')
    parser.add_argument('--check-interval', type=int, default=None, help='''R|
                            If --execute is pbs (or any value besides local) will wait for the job to finish.
                            Interval, in which the script quiries the HPC for the job status.
                            Specify in seconds.
                            ''')
    parser.add_argument('--log-path', type=str, default='.ci-hpc.log', help='''R|
                            If set, will override standard log file location
                            ''')
    parser.add_argument('--log-style', choices=['short', 'long'], default='short', help='''R|
                            Format style of the logger
                            ''')
    parser.add_argument('--log-level', default='info', choices=['debug', 'info', 'warning', 'error'], help='''R|
                            Level of the logger
                            ''')

    parser.add_argument('--watch-commit-limit', type=int, default=None, help='''R|
                            When in 'watch' mode, represents number of commits to load
                            from git log. Bigger number can cause git log to take longer.
                            Smaller number may cause lower resolution, not catching
                            all the changes made.
                            ''')
    parser.add_argument('--watch-commit-policy', choices=['every-commit', 'commit-per-day'], default=None, help='''R|
                            When in 'watch' mode, represents number of commits to load
                            from git log. Bigger number can cause git log to take longer.
                            Smaller number may cause lower resolution, not catching
                            all the changes made.
                            ''')

    parser.add_argument('--tty', default=False, action='store_true', help='''R|
                            If set, will force tty human readable mode
                            ''')
    parser.add_argument('step', type=str, nargs='*', default=['install', 'test'])

    # parse given arguments
    args = parser.parse_args(cmd_args)
    return args


def main(cmd_args=None):
    from cihpc.common.logging import basic_config
    from cihpc.cfg.config import global_configuration
    from cihpc.common.utils.git import Git
    from cihpc.git_tools import CommitHistoryExecutor
    from cihpc.cfg.cfgutil import find_valid_configuration

    import cihpc.cfg.cfgutil as cfgutil

    from cihpc.git_tools.utils import ArgConstructor, CommitBrowser
    from cihpc.common.utils.parsing import defaultdict_type, convert_project_arguments
    from cihpc.common.utils import strings as strings_utils

    from cihpc.core.processing.project import ProcessProject
    from cihpc.core.structures.project import Project
    from cihpc.core.execution import SeparateExecutor, ExecutionFactor

    # parse args
    args = parse_args(cmd_args)

    # configure the logging
    basic_config(
        level=getattr(logging, args.log_level.upper()),
        log_path=args.log_path,
        stream=sys.stdout
    )

    logger = logging.getLogger(__name__)

    # force tty mode if set
    if args.tty:
        global_configuration.tty = True

    # -------------------------------------------------------

    # all the paths depend on the project name
    project_name = args.project

    logger.info('running cihpc for the project %s' % project_name)
    logger.debug('app args: %s', str(args))

    # convert list ["key:value", "key2:value2", ...] to dict {key:value, key2:value2}
    # default value for this dictionary is string value 'master'
    args.git_branch = defaultdict_type(args.git_branch, 'master', project_name)

    # default value for this dictionary is string value ''
    args.git_commit = defaultdict_type(args.git_commit, '', project_name)

    # all configuration files are cfg/<project-name> directory if not set otherwise
    project_dir = find_valid_configuration(
        args.config_dir,
        os.path.join(global_configuration.cfg, project_name),
        os.path.abspath(project_name),
        file='config.yaml',
    )

    if not project_dir:
        logger.error('no valid configuration found for the project %s\n'
                     'the paths that were tried: \n  %s', project_name,
                     '\n  '.join([
                         '1) --config-dir      ' + str(args.config_dir),
                         '2) ./cfg/<project>   ' + os.path.join(global_configuration.cfg, project_name),
                         '3) ./<project>       ' + os.path.abspath(project_name)
                     ]))
        sys.exit(1)
    else:
        logger.info('determined config dir: %s' % project_dir)

    # execute on demand using pbs/local or other system
    if args.pbs:
        script_content = SeparateExecutor.get_script(
            args, os.path.join(project_dir, 'execute.sh')
        )

        executor = ExecutionFactor.create(
            args.pbs,
            script_content
        )
        executor.submit()

        if args.timeout:
            result = executor.wait(args.timeout, kill=True)
            if result:
                sys.exit(0)
            else:
                sys.exit(1)
        sys.exit(0)

    if global_configuration.tty:
        logger.info('started ci-hpc in a tty mode')
    else:
        logger.info('started ci-hpc *not* in a tty mode')

    # this file contains only variables which can be used in config.yaml
    variables_path = os.path.join(project_dir, 'variables.yaml')
    # this file contains all the sections and steps for installation and testing
    config_path = os.path.join(project_dir, 'config.yaml')

    # update cpu count
    variables = cfgutil.load_config(variables_path)
    # variables['cpu-count'] = args.cpu_count

    global_configuration.project_name = project_name
    global_configuration.project_cfg_dir = project_dir
    global_configuration.project_cfg = config_path

    # -----------------------------------------------------------------

    # otherwise load configs
    project_configs = cfgutil.configure_file(config_path, variables)
    for project_config in project_configs:
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

        project = ProcessProject(project_definition)
        logger.info('processing project %s, section %s', project_name, args.step)

        if 'watch' in args.step:
            if not global_configuration.project_git:
                logger.error('no repository provided')
                exit(0)

            project_commit_format = global_configuration.project_git.commit
            if not project_commit_format or not str(project_commit_format).strip():
                logger.error('project repository must be configurable via <arg.commit.foobar> placeholder')

            project_commit_format = str(project_commit_format).strip()
            if project_commit_format.startswith('<arg.commit.') and project_commit_format.endswith('>'):
                commit_field = project_commit_format[len('<arg.commit.'):-1]
                fixed_args = [sys.executable, global_configuration.main_py] \
                             + convert_project_arguments(args, excludes=['step'])

                args_constructor = ArgConstructor(fixed_args, commit_field)
                commit_browser = CommitBrowser(
                    Git(global_configuration.project_git),
                    limit=args.watch_commit_limit,
                    commit_policy=args.watch_commit_policy,
                )
                logger.info('analyzing last %d commits, commit pick policy: %s' % (
                    commit_browser.limit, commit_browser.commit_policy))
                service = CommitHistoryExecutor(project_name, args_constructor, commit_browser)
                service.run()
                exit(0)

        if 'install' in args.step:
            project.process_section(project_definition.install)

        if 'test' in args.step:
            project.process_section(project_definition.test)
