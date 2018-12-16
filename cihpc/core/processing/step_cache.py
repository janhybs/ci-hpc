#!/usr/bin/python
# author: Jan Hybs

import logging

from cihpc.common.utils.git import Git
from cihpc.core.processing.step_git import configure_git


logger = logging.getLogger(__name__)

import os
import shutil
from cihpc.common.utils.datautils import recursive_get
from cihpc.cfg.cfgutil import configure_object, configure_string


class ProcessStepCache(object):
    _arg_map = {
        'arg.branch'  : 'b',
        'arg.commit'  : 'c',
        'project-name': '-',
    }

    def __init__(self, step_cache, step_git, global_args=None, cwd='.'):
        """
        Function will clone given git
        and will checkout to a given branch and commit
        :type step_cache: cihpc.core.structures.project_step_cache.ProjectStepCache
        :type step_git: list[cihpc.core.structures.project_step_git.ProjectStepGit]
        :type global_args: dict
        """

        self.global_args = global_args
        self.step_cache = step_cache
        self.step_git = step_git
        self.value = None
        self.cwd = os.path.abspath(cwd)

        self.storage = configure_string(
            self.step_cache.storage,
            self.global_args
        )
        self.directories = configure_object(
            self.step_cache.directories,
            self.global_args
        )

        self.fields = self.step_cache.fields or (
            'project-name',
        )
        attributes = list()
        for f in self.fields:
            recursive_value = recursive_get(self.global_args, f)
            if recursive_value:
                attributes.append(
                    (self._arg_map.get(f, f), str(recursive_value))
                )

        for git in step_git:
            git_control = Git(configure_git(git, self.global_args))

            # arguments are more important than actual git repo state
            if git_control.git.commit:
                attributes.append((git.repo, git_control.git.commit[:10]))
            else:
                attributes.append((git.repo, (git_control.commit or 'none')[:10]))

        self.value = ','.join(['%s-%s' % x for x in attributes])
        self.location = os.path.join(self.storage, self.value)

    def exists(self):
        if os.path.exists(self.location) and os.path.isdir(self.location):
            return True
        return False

    def restore(self):
        for dirname in self.directories:
            from_dir = os.path.join(self.location, dirname)
            to_dir = os.path.join(self.cwd, dirname)
            logger.debug('restoring cache dir %s' % dirname)

            if os.path.exists(to_dir):
                logger.debug('rm tree %s' % to_dir)
                shutil.rmtree(to_dir)
            shutil.copytree(from_dir, to_dir)

    def save(self):
        for dirname in self.directories:
            from_dir = os.path.join(self.cwd, dirname)
            to_dir = os.path.join(self.location, dirname)
            logger.debug('saving cache dir %s' % dirname)

            if os.path.exists(to_dir):
                logger.debug('rm tree %s' % to_dir)
                shutil.rmtree(to_dir)
            shutil.copytree(from_dir, to_dir)

    def __repr__(self):
        return 'ProcessStepCache(%s)' % self.value
