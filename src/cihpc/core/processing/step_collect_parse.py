#!/usr/bin/python
# author: Jan Hybs

from loguru import logger


def process_step_collect_parse(project, step, process_result, format_args=None):
    """
    Function will parse the file from an output
    :type step:           structures.project_step.ProjectStep
    :type project:        structures.project.Project
    :type process_result: proc.step.step_shell.ProcessStepResult
    """

    logger.debug(f'parsing output artifacts')
    if not process_result.output:
        logger.warning(f'Empty output received, make sure the field ouutput is set to \n'
                       f'output: log+stdout \n'
                       f'in order to capture output of the shell step')
        return []

    index = 0
    output = process_result.output
    start = step.collect.parse.start
    stop = step.collect.parse.start
    ls, le = len(start), len(stop)

    length = len(output)
    reports = list()

    while True:
        # no more reports found
        s = output.find(start, index, length)
        if s == -1:
            break

        # broken report
        e = output.find(stop, s + 1, length)
        if e == -1:
            logger.debug(f'could not find end of the report file while parsing the output')
            break

        index = e + le + 1
        # try to parse the data or skip it
        reports.append(output[s + ls:e].strip())

    return reports
