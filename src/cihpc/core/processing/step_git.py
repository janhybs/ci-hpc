#!/usr/bin/python
# author: Jan Hybs

from loguru import logger

from cihpc.cfg.cfgutil import configure_string
from cihpc.common.utils.git import Git



def process_step_git(step_git, global_args=None):
    """
    Function will clone given git
    and will checkout to a given branch and commit
    :type step_git: list[structures.project_step_git.ProjectStepGit]
    """
    logger.debug(f'processing git repos')
    for git in step_git:
        git_control = Git(configure_git(git, global_args))
        logger.debug(f'initializing git {git.repo} to ({git.branch}, {git.commit})')
        git_control.clone()
        git_control.checkout()
        git_control.info()


def configure_git(git, global_args):
    if global_args:
        git.branch = configure_string(git.branch, global_args)
        git.commit = configure_string(git.commit, global_args)

    return git
