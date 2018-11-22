#!/bin/python3
# author: Jan Hybs

import tests

from unittest import TestCase
from structures.project_step_repeat import ProjectStepRepeat


class TestProjectStepRepeat(TestCase):

    def test_init(self):
        ProjectStepRepeat(None)
        ProjectStepRepeat(5)
        ProjectStepRepeat({'exactly': 10})
        ProjectStepRepeat({'exactly': 10, 'no-less-than': 15})

        with self.assertRaises(ValueError):
            ProjectStepRepeat(True)

        with self.assertRaises(ValueError):
            ProjectStepRepeat(dict())

    def test_value(self):
        repeat = ProjectStepRepeat(None)
        self.assertEqual(repeat.fixed_value, 1)
        self.assertEqual(repeat.dynamic_value, None)
        self.assertEqual(repeat.value, 1)

        repeat = ProjectStepRepeat(5)
        self.assertEqual(repeat.fixed_value, 5)
        self.assertEqual(repeat.dynamic_value, None)
        self.assertEqual(repeat.value, 5)

        data = {'exactly': 10}
        repeat = ProjectStepRepeat(data)
        self.assertEqual(repeat.fixed_value, 10)
        self.assertEqual(repeat.dynamic_value, None)
        self.assertEqual(repeat.value, 10)

        data = {'exactly': 10, 'no-less-than': 15}
        repeat = ProjectStepRepeat(data)
        self.assertEqual(repeat.fixed_value, 10)
        self.assertEqual(repeat.dynamic_value, 15)
        self.assertEqual(repeat.value, 15)
        repeat._remains = 5  # simulate commit load
        self.assertEqual(repeat.value, 5)

    def test_is_complex(self):
        repeat = ProjectStepRepeat(None)
        self.assertFalse(repeat.is_complex())

        repeat = ProjectStepRepeat(5)
        self.assertFalse(repeat.is_complex())

        data = {'exactly': 10}
        repeat = ProjectStepRepeat(data)
        self.assertFalse(repeat.is_complex())

        data = {'exactly': 10, 'no-less-than': 15}
        repeat = ProjectStepRepeat(data)
        self.assertTrue(repeat.is_complex())

        data = {'no-less-than': 15}
        repeat = ProjectStepRepeat(data)
        self.assertTrue(repeat.is_complex())
