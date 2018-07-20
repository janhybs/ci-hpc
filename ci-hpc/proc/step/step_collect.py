#!/usr/bin/python
# author: Jan Hybs


import glob
import os
import importlib
from datetime import datetime

from utils.config import configure_object
from utils.logging import logger
from utils.config import configure_string


def process_step_collect(step, format_args=None):
    """
    Function will collect artifacts for the given step
    :type step:           structures.project_step.ProjectStep
    """
    logger.debug('collecting artifacts')
    files = glob.glob(step.collect.files, recursive=True)
    logger.debug('found %d files to collect', len(files))

    module = importlib.import_module(step.collect.module)
    CollectModule = module.CollectModule

    if files:
        # get git information
        if step.collect.repo:
            CollectModule.init_collection(step.collect.repo)

        # enrich system section
        if step.collect.extra:
            extra = configure_object(step.collect.extra, format_args)
            CollectModule.add_extra(extra)

        # create instance of the CollectModule
        profiler = CollectModule()
        results = list()

        timers_info = []
        timers_total = 0
        for file in files:
            with logger:
                collect_result = profiler.process_file(file)
                timers_total += len(collect_result.items)
                timers_info.append((os.path.basename(file), len(collect_result.items)))
                results.append(collect_result)
        
        with logger:
            for file, timers in timers_info:
                logger.debug('%20s: %5d timers found', file, timers)
            logger.info('artifacts: found %d timer(s) in %d file(s)', len(files), timers_total)
            
        # insert artifacts into db
        if step.collect.save_to_db:
            CollectModule.save_to_db(results)

        # move results to they are not processed twice
        if step.collect.move_to:
            move_to = configure_string(step.collect.move_to, format_args)
            logger.debug('moving %d files to %s', len(files), move_to)

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
