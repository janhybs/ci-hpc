#!/bin/python3
# author: Jan Hybs

import os
import sys
import shutil
import subprocess


class Git(object):
    def __init__(self, url, dir=None, **kwargs):
        self.url = url
        self.dir = dir
        self.repo = os.path.basename(self.url).split('.')[0]
        self.dir = os.path.abspath(os.path.join(os.getcwd(), self.repo))
        self.remove_before_checkout = kwargs.get('remove-before-checkout', False)

    def _construct(self, start, *rest, shell=False):
        args = start.split() if type(start) is str else start
        args.extend(rest)
        return ' '.join(args) if shell else args

    def _execute(self, *args, **kwargs):
        command = self._construct(*args, shell=kwargs.get('shell', False))
        print('$>', self._construct(*args, shell=True))
        sys.stdout.flush()
        if os.path.exists(self.dir):
            return subprocess.Popen(command, **kwargs, cwd=self.dir)
        else:
            return subprocess.Popen(command, **kwargs)

    def clone(self):
        if self.remove_before_checkout:
            shutil.rmtree(self.dir, ignore_errors=True)

        if os.path.exists(self.dir):
            # print('Directory not empty', self.dir, '(git clone skipped)')
            return

        self._execute('git clone', self.url, self.dir).wait()

    def checkout(self, commit='', branch='master'):
        if branch:
            branch = branch.split('/')[-1]

        print('Processing repo {self.repo}'.format(self=self))
        print('-'*60)
        self._execute('git branch -vv').wait()
        self._execute('git fetch').wait()

        if branch:
            # just in case set remote upstream branch
            # then forcefully checkout to branch
            # and pull the latest changes
            self._execute('git branch --set-upstream-to=origin/%s %s' % (branch, branch)).wait()
            self._execute('git checkout -f', branch).wait()
            self._execute('git pull').wait()

        if commit:
            # if there is a commit specified, we forcefully checkout it out
            head = subprocess.check_output('git rev-parse HEAD'.split(), cwd=self.dir).decode()
            if head != commit:
                self._execute('git checkout -f', commit).wait()
                # create new local branch with given name (if branch is specified)
                # so if someone asks on which branch we are, answer won't be 'detached HEAD'
                if branch:
                    self._execute('git branch -d', branch).wait()
                    self._execute('git checkout -b', branch).wait()

    def info(self):
        print('Repository currently at:')
        self._execute('git branch -vv').wait()
        self._execute('git log -n 10 --graph', '--pretty=format:%h %ar %aN%d %s').wait()
