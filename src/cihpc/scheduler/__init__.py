#!/bin/python3
# author: Jan Hybs
import os
from typing import List

from loguru import logger
from pathlib import Path
import cihpc.core.db as db
from cihpc.core.parsers.schedule_parser import parse_args
from cihpc.core.processing.project import ProcessProject
from cihpc.core.utils import iter_project_definition
from cihpc.common.utils.vcs import HistoryBrowser, GitHistory


def main(cmd_args=None):
    from cihpc.cfg.config import global_configuration

    from cihpc.core.processing.project import ProcessProject

    # parse args
    args = parse_args(cmd_args)

    if args.secret_yaml:
        global_configuration.cfg_secret_path = args.secret_yaml

    actions: List[str] = args.actions

    # -------------------------------------------------------

    for project_definition in iter_project_definition(args):
        # prepare process
        project = ProcessProject(project_definition, initialize_repository=False)
        logger.info(f'processing project {project_definition.name}')
        scheduler = ProjectScheduler(project_definition, actions)

        scheduler.run()


class ProjectScheduler:
    def __init__(self, project, actions: List[str] = None):
        """
        :type project: cihpc.core.structures.project.Project
        """
        self.project = project
        if not self.project.use_database:
            raise ValueError(f'Project {self.project.name} must have database enabled')

        db.CIHPCMongo.set_default(
            db.CIHPCMongo.get(self.project.name)
        )

        if not self.project.git:
            raise ValueError(f'Project {self.project.name} must have git repository set')

        self.browser = HistoryBrowser(
            self.project.git.main_repo.url,
            Path(self.project.git.main_repo.dir),
        )

        self.history: List[GitHistory] = None
        self.actions = actions[:-1]
        self.test_action = actions[-1]
        logger.info(f'Git repo dir: {self.project.git.main_repo.dir}')

    def run(self):
        os.chdir(self.project.git.main_repo.dir)
        hist = list(self.browser.git_history(limit=10))
        self.history= sorted(list(set([h for h in hist])), reverse=True)
        logger.info(f'Found {len(hist)} commits, {len(self.history)} of which are unique')
        total = len(self.history)

        for i, gh in enumerate(self.history):
            logger.critical(f'[{i+1}/{total}] Running commit {gh.short_hexsha}')
            self.project.git.main_repo._commit = str(gh.commit.hexsha)
            self.project.git.main_repo._branch = 'master'  # sadly a single commit can be in several branches

            pp = ProcessProject(self.project, initialize_repository=True)
            test_stage = pp.get_stage_by_name(self.test_action)
            if not test_stage:
                continue

            threads = pp.get_stage_variable_stats(test_stage)
            need_to_run = False
            for need_repeats, db_index in threads:
                if need_repeats > 0:
                    need_to_run = True
                    break

            failed = False
            if not need_to_run:
                logger.warning(f'no need to process this commit')
            else:
                for action in self.actions:
                    logger.info(f'running stage {action}')
                    stage = pp.get_stage_by_name(action)

                    if stage:
                        if not pp.process_stage(stage):
                            # terminate the current build on error
                            logger.error(f"stage {stage.name} failed, breaking")
                            failed = True
                            break

                if not failed:
                    pp.process_stage(test_stage)

    def check_for_new_commits(self, min_reps: int = 0):
        pass


if __name__ == '__main__':
    main()
