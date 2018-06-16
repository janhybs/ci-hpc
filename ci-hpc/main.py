#!/lustre/sw/anaconda/anaconda3/bin/python3
# module load anaconda/python3
# module load singularity/2.4
# module load python-3.6.3-gcc-6.2.0-snvgj45
#/bin/python


# python3 main.py --commit "bf39fb3933bc96061a9cdece73835ac66e171d5a" --branch "origin/master" --repo "https://github.com/janhybs/HPC-CI.git"

import re
import argparse
import os
from collections import defaultdict

import utils.config as cfgutil
from utils.config import Config as cfg
from utils.logging import logger

from proc.project import ProcessProject
from structures.project import Project


def main():
    __dir__ = os.path.abspath(os.path.dirname(__file__))
    __root__ = os.path.dirname(__dir__)
    __cfg__ = os.path.join(__root__, 'cfg')
    __src__ = os.path.join(__root__, 'ci-hpc')

    # create parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--branch', action='append', type=str, default=[])
    parser.add_argument('-c', '--commit',  action='append', type=str, default=[])
    parser.add_argument('-p', '--project', type=str, default='flow123d')
    parser.add_argument('--cpu-count', type=str, default='[1]')
    parser.add_argument('step', type=str, nargs='*', default=['install', 'test'])

    # parse given arguments
    args = parser.parse_args()

    # all the paths depend on the project name
    project_name = args.project

    # all configuration files are cfg/<project-name> directory
    project_dir = os.path.join(__cfg__, project_name)

    # this file contains only variables which can be used in config.yaml
    variables_path = os.path.join(project_dir, 'variables.yaml')
    # this file contains all the sections and steps for installation and testing
    config_path = os.path.join(project_dir, 'config.yaml')
    # this file should be PROTECTED, it may contain passwords and database connection details
    project_path = os.path.join(project_dir, 'secret.yaml')

    # load configuration
    cfg.init(project_path)

    # convert list ["key:value", "key2:value2", ...] to dict {key:value, key2:value2}
    # default value for this dictionary is string value 'master'
    args.branch = dict(tuple(d.split(':', 1)) for d in args.branch)
    args.branch = defaultdict(lambda: 'master', **args.branch)

    # default value for this dictionary is string value ''
    args.commit = dict(tuple(d.split(':', 1)) for d in args.commit)
    args.commit = defaultdict(lambda: '', **args.commit)

    # update cpu count
    variables = cfgutil.load_config(variables_path)
    variables['cpu-count'] = args.cpu_count

    # load config
    project_config = cfgutil.configure_file(config_path, variables)
    logger.info('yaml configuration:')
    logger.info(cfgutil.yaml_dump(project_config), skip_format=True)

    # specify some useful global arguments which will be available in the config file
    global_args = {
        'project-name': project_name,
        'project-dir': project_dir,
        'arg': dict(
            branch=defaultdict(lambda: 'master', **dict(args.branch)),
            commit=defaultdict(lambda: '', **dict(args.commit)),
        )
    }

    # parse config
    project_definition = Project(project_name, **project_config)
    project_definition.global_args.update(global_args)

    project = ProcessProject(project_definition)
    logger.info('Processing project %s, section %s', project_name, args.step)

    # -----------------------------------------------------------------

    if 'install' in args.step:
        project.process_section(project_definition.install)

    if 'test' in args.step:
        project.process_section(project_definition.test)


if __name__ == '__main__':
    main()