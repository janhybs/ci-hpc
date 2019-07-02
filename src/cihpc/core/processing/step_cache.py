#!/usr/bin/python
# author: Jan Hybs

from loguru import logger

from cihpc.common.utils.timer import log_duration
from cihpc.common.utils.git import Git
from cihpc.core.processing.step_git import configure_git


import os
import shutil
from cihpc.common.utils.datautils import recursive_get
from cihpc.cfg.cfgutil import configure_object, configure_string


class ProcessStepCache(object):
    _cache_folder_format = [
        '<project-name>',
        '<git.commit>'
    ]

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

        self.cache_folder_props = configure_object(
            self._cache_folder_format,
            global_args
        )
        cache_folder_name = '-'.join(self.cache_folder_props)

        self.location = os.path.join(self.storage, cache_folder_name)

    def exists(self):
        if os.path.exists(self.location) and os.path.isdir(self.location):
            return True
        return False

    @log_duration()
    def restore(self):
        for dirname in self.directories:
            from_dir = os.path.join(self.location, dirname)
            to_dir = os.path.join(self.cwd, dirname)
            logger.debug('restoring cache dir %s' % dirname)

            if os.path.exists(to_dir):
                logger.debug('rm tree %s' % to_dir)
                shutil.rmtree(to_dir)
            shutil.copytree(from_dir, to_dir)

    @log_duration()
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
