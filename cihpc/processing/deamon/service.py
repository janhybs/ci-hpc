#!/bin/python3
# author: Jan Hybs

import enum
import itertools
import subprocess
import daemon
import lockfile

from cihpc.structures.project_step_git import ProjectStepGit
from cihpc.cfg.config import global_configuration
from cihpc.utils.logging import logger
from cihpc.utils.timer import Timer
from cihpc.vcs.git import Git, Commit


class ArgConstructor(object):
    def __init__(self, fixed_args, commit_field):
        self.fixed_args: list = fixed_args
        self.commit_lambda = lambda x: ['--git-commit', '%s:%s' % (commit_field, x)]

    def construct_arguments(self, commit):
        return self.fixed_args.copy() + self.commit_lambda(commit)


class CommitPolicy(enum.Enum):
    EVERY_COMMIT = 'every-commit'
    COMMIT_PER_DAY = 'commit-per-day'


class CommitBrowser(object):
    def __init__(self, limit=None, commit_policy=None):
        self.limit = limit or 3
        self.commit_policy = CommitPolicy(commit_policy) if commit_policy else CommitPolicy.EVERY_COMMIT
        self.git = Git(ProjectStepGit(
            url=global_configuration.project_git.url,
            stdout=None,
            logging=logger.LEVEL_INFO,
        ))
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
            logger.debug(msg, skip_format=True)

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
            logger.info(msg, skip_format=True)


class WatchService(object):
    def __init__(self, project, args_constructor, commit_browser):
        self.args_constructor: ArgConstructor = args_constructor
        self.commit_browser: CommitBrowser = commit_browser
        self.project: str = project

    def fork(self):
        logger.info('forking the application')
        log_file = open(logger.log_file, 'a')
        with daemon.DaemonContext(
                stderr=log_file,
                working_directory=global_configuration.src,
                pidfile=lockfile.FileLock('/tmp/ci-hpc-%s.pid' % self.project)):
            # set stream to the log file is opened again
            logger.file_handler.stream = None
            self.start()

    def start(self):
        self.commit_browser.load_commits()
        self.commit_browser.pick_commits()

        logger.info('starting commit processing')
        with logger:
            for commit in self.commit_browser.commits:
                logger.info('%s starting' % commit.short_format)
                with Timer(commit.short_format) as timer:
                    with logger:
                        args = self.args_constructor.construct_arguments(commit.hash)
                        logger.info(str(args), skip_format=True)
                        process = subprocess.Popen(args)
                        process.wait()

                logger.info('%s took %s [%d]' % (commit.short_format, timer.pretty_duration, process.returncode))
