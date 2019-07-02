#!/bin/python3
# author: Jan Hybs
import enum
import os
from copy import deepcopy

from loguru import logger

from cihpc.artifacts.modules import system_info
from cihpc.common.utils import strings
from cihpc.common.utils.datautils import dotdict
from cihpc.core import db as db


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


class CIHPCReport(dotdict):
    global_system = dotdict()
    global_git = dotdict()
    global_result = dotdict()
    global_problem = dotdict()
    global_index = dotdict()

    inited = False

    @classmethod
    def init(cls, path_to_repo=None):
        if cls.inited:
            return

        # if path_to_repo:
        #     cls.global_git = CIHPCReportGit.get(path_to_repo)
        # elif global_configuration.project_git:
        #     cls.global_git = CIHPCReportGit.get(global_configuration.project_git.repo)
        # else:
        #     logger.warning('no git repository set')

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
                index=self.global_index.copy(),

                timers=list(),
                libs=list(),
            )
        )

    def copy(self):
        return deepcopy(dict(
            system=self.system,
            problem=self.problem,
            result=self.result,
            git=self.git,
            index=self.get('index'),
            timers=self.timers,
            libs=self.libs

        ))

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
        index:      { ... }
        result:     { ... }
        git:        { ... }
        timers:     [ { ... }, { ... }, ... ]
        libs:       [ { ... }, { ... }, ... ]
    }

    fields 'problem', 'result' and 'timers' should be included in a report file
    fields 'system' and 'git' are automatically obtained
    field 'index' can be set through config.yaml
    field  'libs' is optional
    """

    def __init__(self, project_name):
        self.project_name = project_name

    def save_to_db(self, collect_results):
        """
        Method will insert results into db
        :type collect_results: list[CollectResult]
        """

        logger.debug('saving %d report files to database' % len(collect_results))
        cihpc_mongo = db.CIHPCMongo.get_default()

        results = list()
        for item in collect_results:

            # save logs first
            if item.logs and item.items:
                log_ids = cihpc_mongo.files.insert_many(item.logs).inserted_ids
                logger.debug('inserted %d files' % len(log_ids))
                item.update(log_ids)

            # insert rest to db
            if item.items:
                results.append(cihpc_mongo.reports.insert_many(item.items))
        logger.debug('inserted %d reports' % len(results))
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