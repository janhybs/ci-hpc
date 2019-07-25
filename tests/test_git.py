#!/bin/python3
# author: Jan Hybs

import tests


tests.fix_paths()

import os
from os.path import join, abspath

from unittest import TestCase

from cihpc.common.utils.files import StdoutType
from cihpc.common.utils.git import Git
from cihpc.core.structures.project_step_git import ProjectStepGit


class TestGit(TestCase):
    def test_git_config(self):
        git_config = ProjectStepGit(
            url='https://github.com/janhybs/ci-hpc.git',
        )
        # default values
        self.assertEqual(git_config.branch, 'master')
        self.assertEqual(git_config.commit, '')
        self.assertEqual(git_config.repo, 'ci-hpc')

        git_config = ProjectStepGit(
            url='git@github.com:janhybs/ci-hpc-foobar.git',
            commit='foobar'
        )
        # default values
        self.assertEqual(git_config.branch, 'master')
        self.assertEqual(git_config.commit, 'foobar')
        self.assertEqual(git_config.repo, 'ci-hpc-foobar')

    def test_git(self):
        git_config = ProjectStepGit(
            url='https://github.com/janhybs/ci-hpc.git',
            stdout=StdoutType.NONE,

        )
        git = Git(git_config)
        self.assertEqual(
            abspath(git.dir),
            abspath(join(os.getcwd(), git_config.repo))
        )

        git.info()
        try:
            commits = git.log(5)
            self.assertEqual(len(commits), 5)
            # depends on version of the git available on machine
        except TypeError:
            pass
