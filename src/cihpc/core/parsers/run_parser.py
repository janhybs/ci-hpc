#!/bin/python3
# author: Jan Hybs
import argparse
import enum
import logging


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