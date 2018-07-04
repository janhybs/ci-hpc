#!/usr/bin/python
# author: Jan Hybs


import glob
import os
import importlib
from datetime import datetime

from utils.logging import logger


def process_step_collect(step):
    """
    Function will collect artifacts for the given step
    :type step:           structures.project_step.ProjectStep
    """
    logger.info('collecting artifacts')
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
            CollectModule.add_extra(step.collect.extra)

        # create instance of the CollectModule
        profiler = CollectModule()
        results = list()

        for file in files:
            with logger:
                results.append(profiler.process_file(file))

        # insert artifacts into db
        if step.collect.save_to_db:
            CollectModule.save_to_db(results)

        # move results to they are not processed twice
        if step.collect.move_to:
            now = datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
            move_to = step.collect.move_to.format(datetime=now)
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