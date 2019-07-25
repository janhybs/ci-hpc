#!/bin/python3
# author: Jan Hybs
import argparse
import logging


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
        'actions',
        nargs='*',
        default=None,
        help='''R|
        Actions to run
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
    args.log_level = getattr(logging, args.log_level.upper())
    if args.debug:
        args.log_level = logging.DEBUG
    return args
