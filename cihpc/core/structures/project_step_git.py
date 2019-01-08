#!/usr/bin/python
# author: Jan Hybs


import os
from cihpc.common.utils.files import StdoutType
from cihpc.cfg.config import global_configuration


class ProjectStepGits(list):
    def __init__(self, kwargs):
        super(ProjectStepGits, self).__init__()

        if not kwargs:
            return

        # single git repo
        elif isinstance(kwargs, dict):
            self.append(ProjectStepGit(**kwargs))

        # list of git repos
        elif isinstance(kwargs, list):
            for v in kwargs:
                if isinstance(v, str):
                    git_kw = self.default_kwargs(v)
                    self.append(ProjectStepGit(**git_kw))
                elif isinstance(v, dict):
                    git_kw = self.default_kwargs(v['url'])
                    git_kw.update(v)
                    self.append(ProjectStepGit(**git_kw))
                else:
                    raise ValueError('kwargs must be dictionary or list ro str')

        # just url
        elif isinstance(kwargs, str):
            git_kw = self.default_kwargs(kwargs)
            self.append(ProjectStepGit(**git_kw))
        else:
            raise ValueError('kwargs must be dictionary or list ro str')

    @staticmethod
    def default_kwargs(url):
        repo_name = str(os.path.basename(url).split('.')[0])
        return dict(
            url=url,
            branch='<arg.branch.%s>' % repo_name,
            commit='<arg.commit.%s>' % repo_name,
        )


class ProjectStepGit(object):
    """
    Simple class holding git specification
    Attributes
    ----------
    repo: str
        name of the repository
    """

    def __init__(self, url,
                 branch='master',
                 commit='',
                 level='debug',
                 stdout=StdoutType.DEVNULL,
                 **kwargs):

        self.url = url
        self.branch = branch
        self.commit = commit
        self.logging = level
        self.stdout = stdout.value
        self.remove_before_checkout = kwargs.get('remove-before-checkout', False)

        self.repo = str(os.path.basename(self.url).split('.')[0])

        # optionally mark this repo as main
        if kwargs.get('is-main') or not global_configuration.project_git:
            global_configuration.project_git = self

    def __repr__(self):
        return 'Git(repo=%s)' % self.repo
