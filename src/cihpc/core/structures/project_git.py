#!/bin/python3
# coding=utf-8
# author: Jan Hybs

import os
from typing import Dict
from git import Repo
from loguru import logger


_default_commit = None
_default_branch = None


class ProjectGit:
    """
    :type main_repo: GitSpec
    :type deps: Dict[str, GitSpec]
    """

    def __init__(self, kwargs):
        self.deps = dict()

        if isinstance(kwargs, str):
            self.main_repo = GitSpec(url=kwargs)

        elif isinstance(kwargs, dict):
            self.main_repo = self._from_dict(**kwargs)

        elif isinstance(kwargs, list):
            self.main_repo = self._from_dict(**kwargs[0])
            for dep in kwargs[1:]:
                repo = self._from_dict(**dep)
                self.deps[repo.name] = repo

        else:
            logger.warning('No git repository provided, please specify field "git" in "config.yaml')
            self.main_repo = None
            self.deps = dict()

    def configure(self, kwargs):
        print(kwargs)
        exit(0)

    @classmethod
    def _from_dict(cls, **kwargs):
        return GitSpec(
            kwargs['url'],
            commit=kwargs.get('commit', _default_commit),
            branch=kwargs.get('branch', _default_branch),
        )

    def __repr__(self):
        return f'Git(main={self.main_repo}, deps={self.deps})'


class GitSpec:
    """
    :type repo: git.Repo
    """

    def __init__(self, url, branch=_default_branch, commit=_default_commit, **kwargs):
        self.url = url
        self.name = str(os.path.basename(url).split('.')[0])
        self._branch = branch
        self._commit = commit or None
        self.checkout = kwargs.get('checkout', True)
        self.clean_before_checkout = kwargs.get('clean-before-checkout', False)
        self.dir = None
        self.repo = None

    def initialize(self):
        self.dir = os.path.abspath(os.path.join(os.getcwd(), self.name))
        logger.info(f'Initializing repo {self.name}')

        if not self.checkout:
            self.repo = Repo(self.dir)
        else:
            self.repo = Repo(self.dir) if os.path.exists(self.dir) else Repo.clone_from(self.url, self.dir)
            self.repo.remote().fetch()

            # easy scenario, branch set, commit not
            if self._branch and not self._commit:
                # branch must exists
                self.repo.git.checkout(self._branch)
                self.repo.active_branch.set_tracking_branch(self.repo.remote().refs[self._branch])
                self.repo.remote().pull()

            # also easy, we have the commit but not the branch
            # only the branch name will be **detached**
            elif not self._branch and self._commit:
                self.repo.git.checkout(self._commit)

            # both branch and commit are set
            # we checkout to commit and create local only branch
            elif self._branch and self._commit:
                if self.commit.startswith(self._commit) and self.branch == self._branch:
                    print('we good')

                else:
                    self.repo.git.checkout(self._commit)
                    self.repo.delete_head(self._branch)
                    new_branch = self.repo.create_head(self._branch)
                    self.repo.head.reference = new_branch

            # nothing was specified
            # we go to the latest master
            else:
                self._branch = 'master'
                self.repo.git.checkout(self._branch)
                self.repo.active_branch.set_tracking_branch(self.repo.remote().refs[self._branch])
                self.repo.remote().pull()

    @property
    def branch(self) -> str:
        try:
            return str(self.repo.active_branch.name)
        except:
            return f'detached-at-{self.commit[:8]}'

    @property
    def commit(self) -> str:
        return str(self.repo.head.commit.hexsha)

    @property
    def commit_short(self) -> str:
        return self.commit[:8]

    @property
    def head_commit(self):
        return self.repo.head.commit

    def index_info(self):
        head = self.repo.head
        return f'{self.branch}:{head.commit.hexsha[:8]} by <{head.commit.author}> on {head.commit.authored_datetime}'

    def _checkout(self):
        pass

    def __repr__(self):
        if self.repo:
            return f'Repo({self.url} @ {self.branch}:{self.commit})'
        return f'Repo({self.url} @ {self._branch}:{self._commit})'
