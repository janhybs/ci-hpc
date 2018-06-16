#!/bin/python3
# author: Jan Hybs

import os
import sys
import shutil
import subprocess
from proc.execution import execute


class Git(object):
    """
    :type git: structures.project_step_git.ProjectStepGit
    """
    def __init__(self, git):
        self.git = git
        self.dir = os.path.abspath(os.path.join(os.getcwd(), self.git.repo))

    def clone(self):
        if self.git.remove_before_checkout:
            shutil.rmtree(self.dir, ignore_errors=True)

        if os.path.exists(self.dir):
            # print('Directory not empty', self.dir, '(git clone skipped)')
            return

        execute('git clone', self.git.url, self.dir).wait()

    def checkout(self):
        branch = self.git.branch
        commit = self.git.commit

        if branch:
            branch = branch.replace('origin/', '')

        print('Processing repo {self.git.repo}'.format(self=self))
        print('-'*60)
        execute('git branch -vv').wait()
        execute('git fetch').wait()

        if branch:
            # just in case set remote upstream branch
            # then forcefully checkout to branch
            # and pull the latest changes
            execute('git branch --set-upstream-to=origin/%s %s' % (branch, branch)).wait()
            execute('git checkout -f', branch).wait()
            execute('git pull').wait()

        if commit:
            # if there is a commit specified, we forcefully checkout it out
            head = subprocess.check_output('git rev-parse HEAD'.split(), cwd=self.dir).decode()
            if head != commit:
                execute('git checkout -f', commit).wait()
                # create new local branch with given name (if branch is specified)
                # so if someone asks on which branch we are, answer won't be 'detached HEAD'
                if branch:
                    execute('git branch -d', branch).wait()
                    execute('git checkout -b', branch).wait()

    def info(self):
        print('Repository currently at:')
        execute('git branch -vv').wait()
        execute('git log -n 10 --graph', '--pretty=format:%h %ar %aN%d %s').wait()
