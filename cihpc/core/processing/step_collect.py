#!/usr/bin/python
# author: Jan Hybs


import glob
import importlib
import json
import logging
import os
from collections import namedtuple

import yaml

from cihpc.artifacts.modules import CIHPCReport, AbstractCollectModule
from cihpc.cfg.cfgutil import configure_object, configure_string
from cihpc.core.processing.step_collect_parse import process_step_collect_parse


logger = logging.getLogger(__name__)


def convert_method(type):
    return dict(json=json.loads, yaml=yaml.load).get(type, lambda x: x)


def iter_reports(reports, conversion, is_file):
    index = 0
    for report in reports:
        index += 1

        if is_file:
            with open(report, 'r') as fp:
                try:
                    yield conversion(fp.read()), report
                except Exception as e:
                    continue

        else:
            try:
                yield conversion(report), 'parse-result-%02d' % index
            except Exception as e:
                continue


def process_step_collect(project, step, process_result, format_args=None):
    """
    Function will collect artifacts for the given step
    :type step:           structures.project_step.ProjectStep
    :type project:        structures.project.Project
    :type process_result: proc.step.step_shell.ProcessStepResult
    """
    logger.debug('collecting artifacts')
    result = namedtuple('CollectResult', ['total', 'items'])(total=[], items=[])

    module = importlib.import_module(step.collect.module)
    CollectModule = module.CollectModule

    # obtain git information
    CIHPCReport.init(step.collect.repo)

    # enrich result section
    if step.collect.extra:
        extra = configure_object(step.collect.extra, format_args)
        CIHPCReport.global_problem.update(extra)

    # create instance of the CollectModule
    instance = CollectModule(project.name)  # type: AbstractCollectModule

    # get either yaml or json
    conversion = convert_method(step.collect.type)

    # --------------------------------------------------

    results = list()
    timers_info = []
    timers_total = 0

    if step.collect.parse:
        reports = process_step_collect_parse(project, step, process_result, format_args)
        logger.debug('artifacts: found %d reports to process', len(reports))

        for report, file in iter_reports(reports, conversion, is_file=False):
            try:
                collect_result = instance.process(report, file)
                timers_total += len(collect_result.items)
                timers_info.append((os.path.basename(file), len(collect_result.items)))
                results.append(collect_result)
            except Exception as e:
                logger.warning(
                    'artifact processing failed (parse method) \n'
                    'module: %s\n'
                    'report: %s\n'
                    'file: %s\n', str(CollectModule), str(report), str(file)
                )

        for file, timers in timers_info:
            logger.debug('%20s: %5d timers found', file, timers)
        logger.debug('artifacts: found %d timer(s) in %d file(s)', timers_total, len(reports))

        # insert artifacts into db
        if step.collect.save_to_db:
            instance.save_to_db(results)

    result.total.append(timers_total)
    result.items.append(timers_info)

    # --------------------------------------------------

    results = list()
    timers_info = []
    timers_total = 0

    if step.collect.files:
        files_glob = configure_string(step.collect.files, format_args)
        files = glob.glob(files_glob, recursive=True)
        logger.debug('artifacts: found %d files to process', len(files))

        for report, file in iter_reports(files, conversion, is_file=True):
            try:
                collect_result = instance.process(report, file)
                timers_total += len(collect_result.items)
                timers_info.append((os.path.basename(file), len(collect_result.items)))
                results.append(collect_result)
            except Exception as e:
                logger.warning(
                    'artifact processing failed (files method) \n'
                    'module: %s\n'
                    'report: %s\n'
                    'file: %s\n', str(CollectModule), str(report), str(file)
                )

        for file, timers in timers_info:
            logger.debug('%20s: %5d timers found', file, timers)
        logger.debug('artifacts: found %d timer(s) in %d file(s)', timers_total, len(files))

        # insert artifacts into db
        if step.collect.save_to_db:
            instance.save_to_db(results)

        # move results to they are not processed twice
        if step.collect.move_to:
            move_to = configure_string(step.collect.move_to, format_args)
            logger.debug('artifacts: moving %d files to %s', len(files), move_to)

            for file in files:
                old_filepath = os.path.abspath(file)

                # customize location and prefix of the dir structure if set
                if step.collect.cut_prefix:
                    new_rel_filepath = old_filepath.replace(step.collect.cut_prefix, '').lstrip('/')
                    new_dirname = os.path.join(
                        move_to,
                        os.path.dirname(new_rel_filepath),
                    )
                    new_filepath = os.path.join(new_dirname, os.path.basename(file))
                    os.makedirs(new_dirname, exist_ok=True)
                    os.rename(old_filepath, new_filepath)
                else:
                    new_filepath = os.path.join(
                        move_to,
                        os.path.basename(file)
                    )
                    os.makedirs(move_to, exist_ok=True)
                    os.rename(old_filepath, new_filepath)

    result.total.append(timers_total)
    result.items.append(timers_info)

    return result
