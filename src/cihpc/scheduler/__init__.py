#!/bin/python3
# author: Jan Hybs

import cihpc.core.db as db


def main():
    pass


class TestScheduler:
    def __init__(self, project):
        """
        :type project:  cihpc.core.structures.project.Project
        """
        self.project = project

        if not self.project.use_database:
            raise ValueError(f'Project {self.project.name} must have database enabled')

        db.CIHPCMongo.set_default(
            db.CIHPCMongo.get(self.project.name)
        )

    def check_for_new_commits(self, history: int = 0):
        pass



if __name__ == '__main__':
    main()
