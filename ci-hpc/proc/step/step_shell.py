#!/usr/bin/python
# author: Jan Hybs

import os
import sys
import subprocess as sp
from datetime import datetime
from time import time

import proc.step.step_measure as step_measure
import utils.strings as strings

from files.temp_file import TempFile
from proc import merge_dict
from utils.events import EnterExitEvent
from utils.dynamicio import DynamicIO
from utils.logging import logger
from utils.config import configure_string


class ShellProcessing(object):
    def __init__(self):
        self.init = EnterExitEvent('Init')
        self.shell = EnterExitEvent('Shell')
        self.process = EnterExitEvent('Process')


class ProcessStepResult(object):
    """
    :type process: subprocess.Popen
    """
    def __init__(self):
        self.process = None
        self.duration = None
        self.shell_duration = None
        self.returncode = None
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time()
        self.duration = self.end_time - self.start_time
        return False


def process_step_shell(project, section, step, vars, shell_processing):
    """
    Function will execute shell from given step using specific vars in the process
    :type project:         structures.project.Project
    :type section:         structures.project_section.ProjectSection
    :type step:            structures.project_step.ProjectStep
    :type shell_processing: ShellProcessing
    """
    logger.debug('processing shell script in step %s', step.name)
    format_args = project.global_args

    if vars:
        format_args = merge_dict(
            format_args,
            vars,
        )

    if step.shell:
        # determine tmp dir which will hold all the scripts
        tmp_dir = os.path.join(
            'tmp.%s' % project.name,
            section.ord_name,
            '%d.%s' % (section.index(step) + 1, step.name))

        # if vars are given, we go deeper and create subdirectory for each configuration
        if vars:
            tmp_dir = os.path.join(
                tmp_dir,
                '%d.%d.conf' % (format_args['__current__'], format_args['__total__']))

        # create dir
        os.makedirs(tmp_dir, exist_ok=True)

        # the main script which will be executed, either using bash or with the help of a container
        tmp_sh = TempFile(os.path.join(tmp_dir, 'shell.sh'), verbose=step.verbose)

        # ---------------------------------------------------------------------

        with tmp_sh:
            tmp_sh.write_shebang()

            with shell_processing.init(tmp_sh):
                if project.init_shell:
                    configured = configure_string(project.init_shell, format_args)
                    tmp_sh.write_section('INIT SHELL', configured)

            with shell_processing.shell(tmp_sh):
                configured = configure_string(step.shell, format_args)
                tmp_sh.write(configured)

        # ---------------------------------------------------------------------

        result = ProcessStepResult()
        stream = None if step.show_output else logger.log_file

        with DynamicIO(stream) as fp:
            with shell_processing.process(result):
                if not step.container:
                    logger.info('running vanilla shell script %s', tmp_sh.path)
                    process = sp.Popen(['/bin/bash', tmp_sh.path], stdout=fp, stderr=sp.STDOUT)
                else:
                    tmp_cont = TempFile(os.path.join(tmp_dir, 'cont.sh'), verbose=step.verbose)

                    with tmp_cont:
                        tmp_cont.write_shebang()
                        tmp_cont.write(configure_string(step.container.exec % tmp_sh.path, format_args))

                    logger.info('running container shell script %s', tmp_cont.path)
                    process = sp.Popen(['/bin/bash', tmp_cont.path], stdout=fp, stderr=sp.STDOUT)

                result.process = process
                with result:
                    result.returncode = process.wait()

        return result
