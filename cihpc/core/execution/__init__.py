#!/bin/python3
# author: Jan Hybs

import logging
import os
import re
import subprocess
import sys
import tempfile
import time

from cihpc.cfg import cfgutil
from cihpc.cfg.config import global_configuration
from cihpc.common.utils.parsing import convert_project_arguments
from cihpc.common.utils.timer import DynamicSleep


logger = logging.getLogger(__name__)

_execute_script_dummy = '''
#!/bin/bash

echo "<ci-hpc-install>"
<ci-hpc-install>

echo "<ci-hpc-exec>"
<ci-hpc-exec>

exit $?
'''.strip()


class SeparateExecutor(object):
    """
    :type project_dir: str
    :type execute_path: str
    :type execute_script: str
    """

    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.execute_path = os.path.join(self.project_dir, 'execute.sh')
        self.execute_script = None

        self._kwargs = dict()

    @classmethod
    def get_script(cls, args, execute_path=None):
        install_cmd = cls._generate_install_command(args)
        execute_cmd = cls._generage_execute_command(args)
        execute_script = cls._load_content(execute_path)

        kwargs = {
            'ci-hpc-exec'             : ' '.join([sys.executable, global_configuration.main_py]) + ' ' + execute_cmd,
            'ci-hpc-exec-no-interpret': global_configuration.main_py + ' ' + execute_cmd,
            'ci-hpc-exec-only-args'   : execute_cmd,
            'ci-hpc-install'          : install_cmd,
        }
        return cfgutil.configure_string(
            execute_script,
            kwargs
        )

    @staticmethod
    def _load_content(execute_path):
        if not execute_path or not os.path.exists(execute_path):
            logger.warning('could not found %s\n'
                           'will use a generated one, which may not '
                           'be suitable for every system' % execute_path)

        try:
            with open(execute_path, 'r') as fp:
                return fp.read()
        except IOError as e:
            return _execute_script_dummy

    @staticmethod
    def _generate_install_command(args):
        """
        Parameters
        ----------
        args: argparse.Namespace

        Returns
        -------
        str
            pip3 --user install command

        """
        return 'pip3 install --user -r "%s/requirements.txt"' % global_configuration.root

    @staticmethod
    def _generage_execute_command(args):
        """
        Parameters
        ----------
        args: argparse.Namespace

        Returns
        -------
        str
            cihpc execute command with passed arguments

        """
        cmd_args = convert_project_arguments(args, excludes=('pbs',))
        return ' '.join([str(x) for x in cmd_args])


class AbstractExecutor(object):
    def __init__(self, script_content):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pbs', delete=False)
        self.temp_file.write(script_content)
        self.temp_file.close()
        self.id = None
        logger.info('created temp file for the execution %s' % self.temp_file.name)

    def clean(self):
        os.unlink(self.script_path)

    @property
    def script_path(self):
        return self.temp_file.name

    def kill(self):
        """
        kill the job

        Returns
        -------
        bool
            - True on success
            - False on error
        """
        raise NotImplemented()

    def submit(self):
        """
        submit the job via specific scheduling system

        Raises
        ------
        Exception
            when submit fails
        """
        raise NotImplemented()

    def wait(self, timeout=None, kill=True, check_period=(3.0, 60.0)):
        """
        Method wait for the job to finish or until specified timeout
        Parameters
        ----------
        timeout: float
            timeout is ms

        kill: bool
            if true will kill the job after the timeout

        check_period: float or (float, float)
            how often to check the job status

        Returns
        -------
        bool
            - True if job finished naturally
            - False if killed
            - None if reached the timeout but kill was set to False
        """
        raise NotImplemented()


class LocalExecutor(AbstractExecutor):
    def __init__(self, script_content):
        super(LocalExecutor, self).__init__(script_content)
        self.process = None

    def submit(self):
        try:
            self.process = subprocess.Popen(
                ['bash', self.script_path],
                stderr=subprocess.STDOUT,
                stdout=open(self.script_path+'.out', 'w')
            )
            self.id = str(self.process.pid)
            logger.info('ok, job %s created' % self.id)
            logger.info('stdout available in %s' % (self.script_path + '.out'))
        except Exception as e:
            logger.exception('could not submit the job (error: %s) via file %s' % (str(e), self.script_path))
            raise

    def wait(self, timeout=None, kill=True, check_period=(3.0, 60.0)):
        try:
            self.process.wait(timeout)
            self.clean()
            return self.process.returncode == 0
        except subprocess.TimeoutExpired as e:
            logger.warning('reached the job wait timeout, but the job %s did not finish' % self.id)

            if kill:
                logger.info('killing the job %s' % self.id)
                self.kill()
                self.clean()
                return False
            else:
                logger.info('abandoning wait cycle...')
                return None

    def kill(self):
        self.process.kill()


class PBSProExecutor(AbstractExecutor):

    def wait(self, timeout=None, kill=True, check_period=(3.0, 60.0)):
        start_time = time.time()
        if isinstance(check_period, tuple):
            sleeper = DynamicSleep(*check_period)
        else:
            sleeper = DynamicSleep(check_period, check_period, 1)

        while True:
            if not self._is_running(self.id):
                logger.info('job %s finished' % self.id)
                self.clean()
                return True

            if timeout and (time.time() - start_time) > timeout:
                logger.warning('reached the job wait timeout, but the job %s did not finish' % self.id)

                if kill:
                    logger.info('killing the job %s' % self.id)
                    self.kill()
                    self.clean()
                    return False
                else:
                    logger.info('abandoning wait cycle...')
                    return None

            logger.info('waiting for the job %s to finish')
            time.sleep(sleeper())

    def kill(self):
        try:
            command = ['qdel', self.id]
            returncode = subprocess.check_call(command)
            return returncode == 0
        except subprocess.CalledProcessError as e:
            logger.exception('could not kill the job (error: %s) %s' % (str(e), self.id))
            return False

    def submit(self):
        logger.info('submitting pbs via file %s' % self.script_path)

        try:
            command = ['qsub', self.script_path]
            output = str(subprocess.check_output(command).decode()).strip()
            self.id = self._parse_job_id(output)
            logger.info('ok, job %s created' % self.id)
        except Exception as e:
            logger.exception('could not submit the job (error: %s) via file %s' % (str(e), self.script_path))
            raise

    @staticmethod
    def _is_running(id):
        try:
            command = ['qstat', id]
            returncode = subprocess.check_call(command)
            return returncode == 0
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _parse_job_id(cls, output):
        """
        Method extracts a job id from qsub command's output

        We are assuming the output to be something like:
            jan-hybs@tarkil:~/projects $ qsub foo.pbs
            7978879.arien-pro.ics.muni.cz

        Parameters
        ----------
        output

        Returns
        -------

        """

        try:
            return re.compile('([0-9]+)\.?.*').match(output).group(1)
        except Exception as e:
            logger.error('cannot determine job id from string (error: %s):\n%s' % (str(e), output))
            return None


class ExecutionFactor(object):

    @staticmethod
    def create(pbs, script_content):
        """

        Parameters
        ----------
        pbs: str
            pbs mode such as pbspro or local

        script_content: str
            content of the script

        Returns
        -------
        AbstractExecutor
            an executor instance
        """
        if str(pbs).lower() in ('pbs', 'pbspro'):
            return PBSProExecutor(script_content)

        if str(pbs).lower() in ('local', 'none', 'unix'):
            return LocalExecutor(script_content)

        return None