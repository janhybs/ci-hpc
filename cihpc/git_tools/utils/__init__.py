#!/bin/python3
# author: Jan Hybs
import enum
import itertools
import logging
import subprocess as sp
import re

logger = logging.getLogger(__name__)

from cihpc.cfg import cfgutil
from cihpc.common.utils.git import Commit
from cihpc.common.utils.files.temp_file import TempFile2
import cihpc.common.utils.strings as strings


class CommitPolicy(enum.Enum):
    EVERY_COMMIT = 'every-commit'
    COMMIT_PER_DAY = 'commit-per-day'


class CommitBrowser(object):
    def __init__(self, git, limit=3, commit_policy=None):
        """

        Parameters
        ----------
        git: cihpc.common.utils.git.Git
            Git repo instance
        limit: int
            How many commits to load int git log call. Does not mean how many commits in total
            will be processed, it depends on `commit_policy` value.
        commit_policy
        """

        self.limit = limit or 3
        self.commit_policy = CommitPolicy(commit_policy) if commit_policy else CommitPolicy.EVERY_COMMIT
        self.git = git
        self.all_commits: [Commit] = list()
        self.commits: [Commit] = list()

    def load_commits(self):
        # fetch the latest changes
        self.git.checkout()
        # git log the commits
        self.all_commits = self.git.log(self.limit)

        logger.info('loaded %d commits' % len(self.all_commits))
        day_getter = lambda commit: commit.fs_date.split('-')[0]
        for key, group in itertools.groupby(self.all_commits, key=day_getter):
            msg = '- commits on %s\n' % key.replace('_', '-')
            msg += '\n'.join(['   - %s' % commit for commit in group])
            logger.debug(msg)

    def pick_commits(self):
        self.commits = list()

        logger.info('commits which will be tested (marked with +)')
        day_getter = lambda commit: commit.fs_date.split('-')[0]
        for key, group in itertools.groupby(self.all_commits, key=day_getter):
            msg = '- commits on %s\n' % key.replace('_', '-')
            picked = False
            for commit in group:
                if self.commit_policy is CommitPolicy.EVERY_COMMIT \
                        or (self.commit_policy is CommitPolicy.COMMIT_PER_DAY and not picked):
                    picked = True
                    self.commits.append(commit)
                    msg += '   + %s\n' % commit
                else:
                    msg += '   - %s\n' % commit
            logger.info(msg)


class ArgConstructor(object):
    def __init__(self, fixed_args, commit_field):
        """
        Parameters
        ----------
        fixed_args: list[str]
            fixed arguments which will always be a part of a result argument list
        commit_field: str
            name of the commit field so it can be passed in a
            `--git-commit=commit_field:commit_value` where `commit_value` will be
            supplied later in :func:`construct_arguments`
        """

        self.fixed_args: list = fixed_args
        self.commit_lambda = lambda x: ['--git-commit', '%s:%s' % (commit_field, x)]

    def construct_arguments(self, commit_value):
        return self.fixed_args.copy() + self.commit_lambda(commit_value)


class WebhookTrigger(object):
    _default_action = '\n'.join([
        'echo "received arguments from the webhook"',
        'echo "$@"'
    ])

    def __init__(self, kwargs):
        branches = kwargs.get('branches') or '*'

        if isinstance(branches, str):
            self.branches = [branches]
        elif isinstance(branches, list):
            self.branches = branches
        else:
            raise ValueError('expected type list or str of branches')

        actions = kwargs.get('action') or self._default_action
        if isinstance(actions, str):
            self.actions = [actions]
        elif isinstance(branches, list):
            self.actions = actions
        else:
            raise ValueError('expected type list or str of actions')

    def process(self, payload):
        """
        Parameters
        ----------
        payload: cihpc.common.utils.git.webhooks.push_hook.PushWebhook
            payload to process
        """
        project = payload.repository.name
        commit = payload.after
        branch_full = payload.ref
        branch = strings.startswith_strip(branch_full, 'refs/heads/')
        url = payload.repository.html_url
        rest_args = [project, commit, branch, url]

        match = False
        for b in self.branches:
            b = b.replace('*', '.*')
            match |= bool(re.match(b, branch))
            match |= bool(re.match(b, branch_full))

        if not match:
            return None

        for action in self.actions:
            with TempFile2() as tmp_file:
                tmp_file.write_shebang()
                tmp_file.write(action)

            process = sp.Popen(['bash', tmp_file.path] + rest_args)
            returncode = process.wait()
            tmp_file.remove()

            if returncode != 0:
                logger.error('error while executing trigger script %s: \n%s' % (tmp_file.path, tmp_file.content))
                return returncode

        return 0

    @classmethod
    def from_file(cls, path):
        return cls(cfgutil.yaml_load(cfgutil.read_file(path, '{}')))
