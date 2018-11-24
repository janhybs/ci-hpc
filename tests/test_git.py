#!/bin/python3
# author: Jan Hybs

import os
from os.path import join, abspath

import tests

from unittest import TestCase

from utils.files import StdoutType
from structures.project_step_git import ProjectStepGit
from vcs.git import Git


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
        commits = git.log(5)
        self.assertEqual(len(commits), 5)
