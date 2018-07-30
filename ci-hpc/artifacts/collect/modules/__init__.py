#!/usr/bin/python
# author:   Jan Hybs


import enum
import os

from utils import datautils


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

    def __init__(self, items, logs, log_policy=LogPolicy.ON_ERROR, log_folder=None):
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
    flatten : bool
        whether to flatten keys
    """
    items = list()
    report_copy = report.copy()
    timers = report_copy.pop(unwind_from)
    for timer in timers:
        item = report_copy.copy()
        item[unwind_to] = timer
        if flatten:
            items.append(datautils.flatten(item))
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