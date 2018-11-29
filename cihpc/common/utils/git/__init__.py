#!/bin/python3
# author: Jan Hybs

import datetime
import os
import shutil
import subprocess
import logging


from cihpc.common.utils.files import StdoutType
from cihpc.common.processing import create_execute_command


logger = logging.getLogger(__name__)


class Git(object):
    """
    :type git: cihpc.core.structures.project_step_git.ProjectStepGit
    """

    def __init__(self, git):
        self.git = git
        self.dir = os.path.abspath(os.path.join(os.getcwd(), self.git.repo))
        self.execute = create_execute_command(
            logger_method=getattr(logger, self.git.logging, logger.debug),
            stdout=self.git.stdout,
        )
        self.execute_check_output = create_execute_command(
            logger_method=getattr(logger, self.git.logging, logger.debug),
            stdout=StdoutType.PIPE.value,
        )

    def fetch(self):
        self.execute('git fetch', dir=self.dir).wait()

    def clone(self):
        if self.git.remove_before_checkout:
            shutil.rmtree(self.dir, ignore_errors=True)

        if os.path.exists(self.dir):
            # print('Directory not empty', self.dir, '(git clone skipped)')
            return

        self.execute('git clone', self.git.url, self.dir).wait()

    def checkout(self):
        branch = self.git.branch
        commit = self.git.commit

        if branch:
            branch = branch.replace('origin/', '')

        logger.info(
            'Git checkout repo={self.git.repo} to branch={self.git.branch}, commit={self.git.commit}'.format(self=self))
        self.execute("git config core.pager", "", dir=self.dir)  # turn of less pager
        self.execute('pwd', dir=self.dir).wait()
        self.execute('git branch -vv', dir=self.dir).wait()
        self.execute('git fetch', dir=self.dir).wait()

        if branch:
            # just in case set remote upstream branch
            # then forcefully checkout to branch
            # and pull the latest changes
            self.execute('git branch --set-upstream-to=origin/%s %s' % (branch, branch), dir=self.dir).wait()
            self.execute('git checkout -f', branch, dir=self.dir).wait()
            self.execute('git pull', dir=self.dir).wait()

        if commit:
            # if there is a commit specified, we forcefully checkout it out
            head = subprocess.check_output('git rev-parse HEAD'.split(), cwd=self.dir).decode()
            if head != commit:
                self.execute('git checkout -f', commit, dir=self.dir).wait()
                # create new local branch with given name (if branch is specified)
                # so if someone asks on which branch we are, answer won't be 'detached HEAD'
                if branch:
                    self.execute('git branch -d', branch, dir=self.dir).wait()
                    self.execute('git checkout -b', branch, dir=self.dir).wait()

    def info(self):
        logger.debug('Repository currently at:')
        self.execute('git branch -vv', dir=self.dir).wait()
        self.execute('git log -n 10 --graph', '--pretty=format:%h %ar %aN%d %s', dir=self.dir).wait()

    def log(self, limit=50, branch='master'):
        command = 'git log -n {limit} {format} {branch}'.format(
            limit=limit,
            branch=branch,
            format=Commit.git_log_format
        )
        o, e = self.execute_check_output(command, dir=self.dir).communicate(timeout=10)
        lines = [] if not o else o.decode().splitlines()
        commits = list()
        for line in lines:
            commits.append(Commit(*line.split('|', 7)))
        return commits


class Commit(object):
    git_log_format = '--format=%H|%h|%an|%ae|%ar|%at|%D|%s'

    def __init__(self, hash, short_hash, author, email, rel_date, timestamp, refs, message):
        self.hash = hash
        self.short_hash = short_hash
        self.author = author
        self.email = email
        self.rel_date = rel_date
        self.timestamp = int(timestamp)
        self.fs_date = datetime.datetime.fromtimestamp(self.timestamp).strftime('%Y_%m_%d-%H_%M_%S')
        self.refs = refs.split(', ')
        self.message = message

    @property
    def short_format(self):
        return 'commit({self.short_hash} by {self.author}, {self.rel_date})'.format(self=self)

    def __repr__(self):
        return 'Commit({self.short_hash} {self.fs_date} by {self.author}, [{self.message}], {self.rel_date})'.format(
            self=self)
