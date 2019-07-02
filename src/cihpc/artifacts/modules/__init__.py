#!/usr/bin/python
# author:   Jan Hybs


from cihpc.common.utils import datautils


def system_info():
    """
    Function will return system info and as a dict
    """
    import subprocess

    def run(cmd, line=None):
        lines = subprocess.check_output(cmd, shell=True).decode().strip().splitlines()
        if line:
            for l in lines:
                if l.startswith(line):
                    return l[len(line):].replace('"', '')
        return lines[0].replace('"', '')

    return dict(
        name=run('uname'),
        hostname=run('hostname'),
        os_name=run('cat /etc/*-release', 'VERSION='),
        os_version=run('cat /etc/*-release', 'NAME='),
        username=run('echo $(whoami):$(id -u):$(id -g)'),
    )


def unwind_report(report, unwind_from='timers', unwind_to='timer', flatten=False):
    """
    Method will convert flatten json report format to a list of reports

    Parameters
    ----------
    report : dict
        object which will be unwinded
    unwind_from : str
        key name which contains list of values
    unwind_to : str
        under what name to store list values
    flatten : str
        if set, will flatten the documents using this value as separator
    """
    items = list()
    report_copy = report.copy()
    timers = report_copy.pop(unwind_from)
    for timer in timers:
        item = report_copy.copy()
        item[unwind_to] = timer
        if flatten:
            items.append(datautils.flatten(item, sep=flatten))
        else:
            items.append(item)
    return items


def unwind_reports(reports, unwind_from='timers', unwind_to='timer', flatten=False):
    """
    Method will convert flatten json reports format to a list of reports

    Parameters
    ----------
    reports : list[dict]
        objects which will be unwinded
    unwind_from : str
        key name which contains list of values
    unwind_to : str
        under what name to store list values
    flatten : str
        if set, will flatten the documents using this value as separator

    """
    items = list()
    for report in reports:
        items.extend(unwind_report(report, unwind_from, unwind_to, flatten))
    return items


def parse_output(out, line=None):
    """
    Function will parse given output and if some line starts with 'line', if will be removed
    Parameters
    ----------
    out : bytes
        output from subprocess.check_output
    line : str
        prefix which will be removed
    """
    lines = out.decode().strip().splitlines()
    if line:
        for l in lines:
            if l.startswith(line):
                return l[len(line):].replace('"', '')
    return lines[0].replace('"', '')


# class CIHPCReportGit(dict):
#     instances = dict()
#
#     @staticmethod
#     def create(repo: str):
#         """
#         will try to determine branch/commit
#
#         Parameters
#         ----------
#         repo : str
#             a path to a dir or file located within git repository
#         Returns
#         -------
#         CIHPCReportGit
#         """
#
#         root = repo
#         if os.path.isfile(repo):
#             root = os.path.dirname(repo)
#
#         repo_name = parse_output(
#             check_output('basename `git rev-parse --show-toplevel`', shell=True, cwd=root)
#         )
#         try:
#             branch = parse_output(
#                 check_output('git symbolic-ref --short -q HEAD', shell=True, cwd=root)
#             )
#         except Exception as e:
#             branch = 'HEAD'
#
#         commit = parse_output(
#             check_output('git rev-parse HEAD', shell=True, cwd=root)
#         )
#         tag = parse_output(
#             check_output('git describe --tags --always', shell=True, cwd=root)
#         )
#         timestamp = int(parse_output(
#             check_output('git show -s --format=%%ct %s' % commit, shell=True, cwd=root)
#         ))
#         logger.debug('current git ord of *%s* is at:\n'
#                      'commit=%s, branch=%s', repo, commit, branch)
#
#         git = CIHPCReportGit()
#         git.update(
#             dict(
#                 name=repo_name,
#                 branch=branch,
#                 commit=commit,
#                 tag=tag,
#                 timestamp=timestamp,
#                 datetime=datetime.datetime.fromtimestamp(float(timestamp)),
#             )
#         )
#         return git
#
#     @classmethod
#     def current_commit(cls):
#         if global_configuration.project_git:
#             return cls.get(global_configuration.project_git.repo).commit
#         return None
#
#     @classmethod
#     def get(cls, repo):
#         """
#         :rtype: CIHPCReportGit
#         :return: CIHPCReportGit
#         """
#         if not repo:
#             raise ValueError('Expected a valid repository value')
#
#         # assuming we are in a <workdir>
#         if repo not in cls.instances:
#             cls.instances[repo] = cls.create(repo)
#         return cls.instances[repo]
#
#     @classmethod
#     def has(cls, repo: str):
#         return repo in cls.instances
#
#     def __init__(self):
#         super(CIHPCReportGit, self).__init__()
#         self.update(
#             dict(
#                 name=None,
#                 branch=None,
#                 commit=None,
#                 tag=None,
#                 timestamp=None,
#                 datetime=None,
#             )
#         )
#
#     @property
#     def name(self):
#         """
#         Returns
#         -------
#         str
#             a name of the repository
#         """
#         return self['name']
#
#     @name.setter
#     def name(self, value):
#         self['name'] = value
#
#     @property
#     def branch(self):
#         """
#         Returns
#         -------
#         str
#             a current branch (of the HEAD)
#         """
#         return self['branch']
#
#     @branch.setter
#     def branch(self, value):
#         self['branch'] = value
#
#     @property
#     def commit(self):
#         """
#         Returns
#         -------
#         str
#             a current commit (of the HEAD)
#         """
#         return self['commit']
#
#     @commit.setter
#     def commit(self, value):
#         self['commit'] = value
#
#     @property
#     def timestamp(self):
#         """
#         Returns
#         -------
#         str
#             a timestamp of the current commit
#         """
#         return self['timestamp']
#
#     @timestamp.setter
#     def timestamp(self, value):
#         self['timestamp'] = value
#
#     @property
#     def datetime(self):
#         """
#         Returns
#         -------
#         str
#             a datetime of the current commit
#         """
#         return self['datetime']
#
#     @datetime.setter
#     def datetime(self, value):
#         self['datetime'] = value
