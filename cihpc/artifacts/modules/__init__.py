#!/usr/bin/python
# author:   Jan Hybs


import datetime
import enum
import logging
import os
from subprocess import check_output

from cihpc.cfg.config import global_configuration
from cihpc.common.utils import datautils, strings
from cihpc.common.utils.datautils import dotdict
from cihpc.core.db import CIHPCMongo


logger = logging.getLogger(__name__)


class ICollectTool(object):
    """
    Class ICollectTool is abstract class for any collection tool
    """

    include = None
    exclude = None

    def process_file(self, f: str) -> list:
        raise NotImplemented('Method must be implemented')


class LogPolicy(enum.Enum):
    ON_ERROR = 1
    ALWAYS = 2
    NEVER = 3


class CollectResult(object):
    """
    Class CollectResult is simple crate for holding result from
     collect tool
    :type items           : list[dict]
    :type logs            : list[dict]
    :type logs_updated    : list[dict]
    """

    def __init__(self, items, logs=list(), log_policy=LogPolicy.ON_ERROR, log_folder=None):
        """

        :type logs:         list[str]
        :type log_folder:   str
        :type log_policy:   LogPolicy
        """
        self.items = items
        self.logs = []
        self.logs_updated = []

        if log_policy is LogPolicy.NEVER:
            logs = []
        elif log_policy is LogPolicy.ALWAYS:
            pass
        elif log_policy is LogPolicy.ON_ERROR:
            try:
                rc = items[0].get('problem', {}).get('returncode', 1)
            except:
                rc = 1

            if rc in (0, None):
                logs = []

        for log_file in logs:
            log = self._read_log(log_file)
            self.logs.append(dict(
                filename=log_file.replace(log_folder, '').strip('/'),
                data=log
            ))

    def update(self, log_ids: list, dest='logs'):
        """
        Method updates items with specific mongo ids
        :param log_ids:
        :param dest:
        :return:
        """
        self.logs_updated = []
        for i in range(len(log_ids)):
            self.logs_updated.append(dict(
                filename=self.logs[i].get('filename'),
                data=log_ids[i],
                filesize=len(self.logs[i].get('data')) if self.logs[i].get('data') else 0,
            ))

        for item in self.items:
            item[dest] = self.logs_updated

    @classmethod
    def _read_log(cls, log_file: str):
        if os.path.exists(log_file):
            return open(log_file, 'rb').read()
        return None


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


class CIHPCReportGit(dict):
    instances = dict()

    @staticmethod
    def create(repo: str):
        """
        will try to determine branch/commit

        Parameters
        ----------
        repo : str
            a path to a dir or file located within git repository
        Returns
        -------
        CIHPCReportGit
        """

        root = repo
        if os.path.isfile(repo):
            root = os.path.dirname(repo)

        repo_name = parse_output(
            check_output('basename `git rev-parse --show-toplevel`', shell=True, cwd=root)
        )
        try:
            branch = parse_output(
                check_output('git symbolic-ref --short -q HEAD', shell=True, cwd=root)
            )
        except Exception as e:
            branch = 'HEAD'

        commit = parse_output(
            check_output('git rev-parse HEAD', shell=True, cwd=root)
        )
        timestamp = int(parse_output(
            check_output('git show -s --format=%%ct %s' % commit, shell=True, cwd=root)
        ))
        logger.info('current git index of *%s* is at:\n'
                    'commit=%s, branch=%s', repo, commit, branch)

        git = CIHPCReportGit()
        git.update(
            dict(
                name=repo_name,
                branch=branch,
                commit=commit,
                timestamp=timestamp,
                datetime=datetime.datetime.fromtimestamp(float(timestamp)),
            )
        )
        return git

    @classmethod
    def current_commit(cls):
        if global_configuration.project_git:
            return cls.get(global_configuration.project_git.repo).commit
        return None

    @classmethod
    def get(cls, repo):
        """
        :rtype: CIHPCReportGit
        :return: CIHPCReportGit
        """
        if not repo:
            raise ValueError('Expected a valid repository value')

        # assuming we are in a <workdir>
        if repo not in cls.instances:
            cls.instances[repo] = cls.create(repo)
        return cls.instances[repo]

    @classmethod
    def has(cls, repo: str):
        return repo in cls.instances

    def __init__(self):
        super(CIHPCReportGit, self).__init__()
        self.update(
            dict(
                name=None,
                branch=None,
                commit=None,
                timestamp=None,
                datetime=None,
            )
        )

    @property
    def name(self):
        """
        Returns
        -------
        str
            a name of the repository
        """
        return self['name']

    @name.setter
    def name(self, value):
        self['name'] = value

    @property
    def branch(self):
        """
        Returns
        -------
        str
            a current branch (of the HEAD)
        """
        return self['branch']

    @branch.setter
    def branch(self, value):
        self['branch'] = value

    @property
    def commit(self):
        """
        Returns
        -------
        str
            a current commit (of the HEAD)
        """
        return self['commit']

    @commit.setter
    def commit(self, value):
        self['commit'] = value

    @property
    def timestamp(self):
        """
        Returns
        -------
        str
            a timestamp of the current commit
        """
        return self['timestamp']

    @timestamp.setter
    def timestamp(self, value):
        self['timestamp'] = value

    @property
    def datetime(self):
        """
        Returns
        -------
        str
            a datetime of the current commit
        """
        return self['datetime']

    @datetime.setter
    def datetime(self, value):
        self['datetime'] = value


class CIHPCReport(dotdict):
    global_system = dotdict()
    global_git = CIHPCReportGit()
    global_result = dotdict()
    global_problem = dotdict()

    inited = False

    @classmethod
    def init(cls, path_to_repo=None):
        if cls.inited:
            return

        if path_to_repo:
            cls.global_git = CIHPCReportGit.get(path_to_repo)
        elif global_configuration.project_git:
            cls.global_git = CIHPCReportGit.get(global_configuration.project_git.repo)
        else:
            logger.warning('no git repository set')

        cls.global_system = system_info()
        cls.inited = True

    def __init__(self):
        super(CIHPCReport, self).__init__()
        self.update(
            dict(
                system=self.global_system.copy(),
                git=self.global_git.copy(),
                result=self.global_result.copy(),
                problem=self.global_problem.copy(),

                timers=list(),
                libs=list(),
            )
        )

    def merge(self, report):
        """

        Parameters
        ----------
        report : dict
            a new report which contains more information
        """

        report_copy = report.copy()

        merge_dict = dict(
            system='update',
            problem='update',
            result='update',
            git='update',

            timers='extend',
            libs='extend',
        )
        for key, action in merge_dict.items():
            if key in report_copy:
                getattr(self[key], action)(report_copy.pop(key))
        self.update(report_copy)
        return self

    @property
    def system(self):
        """
        Returns
        -------
        dict
            a system information dictionary
        """
        return self['system']

    @property
    def problem(self):
        """
        Returns
        -------
        dict
            a problem information dictionary
        """
        return self['problem']

    @property
    def result(self):
        """
        Returns
        -------
        dict
            a result information dictionary
        """
        return self['result']

    @property
    def timers(self):
        """
        Returns
        -------
        list[dict]
            a list of timers
        """
        return self['timers']

    @property
    def libs(self):
        """
        Returns
        -------
        list[dict]
            a list of libraries used
        """
        return self['libs']

    @property
    def git(self):
        """
        Returns
        -------
        artifacts.collect.modules.CIHPCReportGit
            a system information dictionary
        """
        return self['git']

    def __repr__(self):
        return strings.to_json(self)


class AbstractCollectModule(object):
    """
    This module excepts a dictionary as a first and only argument to the
    method process

    It simply merges system wide information and given object together
    Assuming the structure of the output report:
    {
        system:     { ... }
        problem:    { ... }
        result:     { ... }
        git:        { ... }
        timers:     [ { ... }, { ... }, ... ]
        libs:       [ { ... }, { ... }, ... ]
    }

    fields 'problem', 'result' and 'timers' should be included in a report file
    fields 'system' and 'git' are automatically obtained
    field  'libs' is optional
    """

    def __init__(self, project_name):
        self.project_name = project_name

    def save_to_db(self, collect_results):
        """
        Method will insert results into db
        :type collect_results: list[CollectResult]
        """

        logger.debug('saving %d report files to database', len(collect_results))
        cihpc_mongo = CIHPCMongo.get(self.project_name)

        results = list()
        for item in collect_results:

            # save logs first
            if item.logs and item.items:
                log_ids = cihpc_mongo.files.insert_many(item.logs).inserted_ids
                logger.debug('inserted %d files', len(log_ids))
                item.update(log_ids)

            # insert rest to db
            if item.items:
                results.append(cihpc_mongo.reports.insert_many(item.items))
        logger.debug('inserted %d reports', len(results))
        return results

    def process(self, object, from_file=None):
        """
        method will process given object and returns a CollectResult.

        Based on a configuration, object can be either dict or str.

        Parameters
        ----------
        object : dict or str
            a report containing timing information
        """
        raise NotImplementedError()

    def convert_fields(self, obj, fields, method, recursive=False):
        """
        Recursively will convert given field props to a given type
        Parameters
        ----------
        obj : dict
            object containing key pair values
        fields: list of Regex
            a list if compiled regular expressions, which designated
            field names which are to be converted
        method : callable
            a method using which is value converted
        recursive : bool
            if True will apply conversion method on recursively
        """
        for key in obj:
            for f in fields:
                if f.match(key):
                    obj[key] = method(obj[key])

        if recursive:
            for k, v in obj.items():
                if isinstance(v, dict):
                    obj[k] = self.convert_fields(v, fields, method, recursive)
                if isinstance(v, list):
                    for i in range(len(v)):
                        if isinstance(v[i], dict):
                            v[i] = self.convert_fields(v[i], fields, method, recursive)
        return obj
