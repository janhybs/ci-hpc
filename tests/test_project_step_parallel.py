#!/bin/python3
# author: Jan Hybs

import tests


tests.fix_paths()

import multiprocessing
from unittest import TestCase
from cihpc.core.structures.project_step_parallel import ProjectStepParallel


class TestProjectStepParallel(TestCase):

    def test_init(self):
        cpu_count = multiprocessing.cpu_count()

        self.assertEqual(ProjectStepParallel(False).cpus, 1)
        self.assertEqual(ProjectStepParallel(None).cpus, 1)
        self.assertEqual(ProjectStepParallel(dict()).cpus, 1)
        self.assertEqual(ProjectStepParallel().cpus, 1)

        self.assertEqual(ProjectStepParallel(True).cpus, cpu_count)
        self.assertEqual(ProjectStepParallel(True).prop, 1)

        self.assertEqual(ProjectStepParallel(dict(cpus='100%')).cpus, cpu_count)
        self.assertEqual(ProjectStepParallel(dict(cpus='all')).cpus, cpu_count)
        self.assertEqual(ProjectStepParallel(dict(cpus='full')).cpus, cpu_count)
        self.assertEqual(ProjectStepParallel(dict(cpus=1.00)).cpus, cpu_count)

        self.assertEqual(ProjectStepParallel(dict(cpus=2, prop=5)).prop, 5)

        if cpu_count > 1:
            self.assertEqual(ProjectStepParallel(dict(cpus=2)).cpus, 2)

