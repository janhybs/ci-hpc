#!/usr/bin/python
# author: Jan Hybs

from cihpc.utils.logging import logger
from cihpc.cfg.cfgutil import configure_string
from cihpc.vcs.git import Git


def process_step_git(step_git, global_args=None):
    """
    Function will clone given git
    and will checkout to a given branch and commit
    :type step_git: list[structures.project_step_git.ProjectStepGit]
    """
    logger.debug('processing git repos')
    for git in step_git:
        with logger:
            if global_args:
                git.branch = configure_string(git.branch, global_args)
                git.commit = configure_string(git.commit, global_args)

            git_control = Git(git)
            logger.debug('initializing git %s to (%s, %s)', git.repo, git.branch, git.commit)
            git_control.clone()
            git_control.checkout()
            git_control.info()
