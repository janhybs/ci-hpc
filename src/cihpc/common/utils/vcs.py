#!/bin/python3
# author: Jan Hybs

import pathlib
import os
from typing import List, Union
from dataclasses import dataclass, field
import maya
from cihpc.core.structures.project_git import GitSpec
from git import Commit, RemoteReference, Head

default_min_age = maya.when('6 months ago')


@dataclass(order=True, unsafe_hash=True, eq=True, repr=False)
class Branch:
    head: Head = field(compare=False, hash=True)
    date: maya.MayaDT = field(compare=True, hash=False)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.date.datetime(naive=True)}, {self.head.name})'


@dataclass(order=True, eq=True, unsafe_hash=True, repr=False)
class GitHistory:
    commit: Commit = field(compare=False, hash=True)
    branch: Branch = field(compare=False, hash=False)
    date: maya.MayaDT = field(compare=True, hash=False)

    @property
    def title(self):
        return str(self.commit.message).splitlines()[0] if self.commit else None

    @property
    def short_hexsha(self):
        return str(self.commit.hexsha)[0:8] if self.commit else None

    def __repr__(self):
        return f'{self.__class__.__name__}([{self.short_hexsha}] {self.date.datetime(naive=True)}, {self.branch.head.name}, {self.title})'

    def pretty_repr(self):
        return f'''[{self.short_hexsha}] {self.date.datetime(naive=True)} {self.branch.head.name},
    {self.title}
'''


class HistoryBrowser:
    def __init__(self, url, repo: pathlib.Path, branch='master'):
        self.repo = repo
        self.branch = branch

        repo_parent = repo.parent
        repo_parent.mkdir(parents=True, exist_ok=True)

        self.git = GitSpec(url=url, dir=repo, branch=branch)
        self.git.initialize()

    def get_active_branches(self, min_age=default_min_age) -> List[Branch]:
        for branch in self.git.repo.remotes.origin.refs:
            head: RemoteReference = branch
            remote_date = maya.MayaDT.from_datetime(head.commit.authored_datetime)
            is_old = min_age is not None and remote_date < min_age
            if is_old:
                continue
            yield Branch(head=head, date=remote_date)

    def iter_revision(self, rev, limit=10) -> List[Commit]:
        for i, cmt in enumerate(self.git.repo.iter_commits(rev=rev)):
            if i >= limit:
                break
            yield cmt

    def commit_surroundings(self, commit: Union[str, Commit]):
        raise NotImplementedError("Not implemented")

        # if isinstance(commit, str):
        #     commit: Commit = self.git.repo.commit(commit)
        #
        # print(commit.committed_datetime, commit.message)

    def git_history(self, revision: str = None, min_age: maya.MayaDT=default_min_age, limit=10):
        if revision is None:
            branches = sorted(self.get_active_branches(min_age), reverse=True)
            for remote_branch in branches:
                for cmt in self.iter_revision(remote_branch.head.name, limit):
                    yield GitHistory(
                        commit=cmt,
                        branch=remote_branch,
                        date=maya.MayaDT.from_datetime(cmt.authored_datetime)
                    )
        else:
            branch_rev: Head = self.git.repo.references[revision]
            branch = Branch(
                head=branch_rev,
                date=maya.MayaDT.from_datetime(branch_rev.commit.authored_datetime)
            )

            for cmt in self.iter_revision(branch_rev.name, limit):
                yield GitHistory(
                    commit=cmt,
                    branch=branch,
                    date = maya.MayaDT.from_datetime(cmt.authored_datetime)
                )
