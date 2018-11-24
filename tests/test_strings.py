#!/bin/python3
# author: Jan Hybs

import tests

from unittest import TestCase
from cihpc.utils import strings


class TestStrings(TestCase):

    def test_to_json(self):
        self.assertEqual(strings.to_json(None), 'null')
        self.assertEqual(strings.to_json(dict()), '{}')
        self.assertEqual(strings.to_json(
            dict(b=1, a=2)),
            '{\n    "a": 2,\n    "b": 1\n}'
        )

        import numpy as np

        self.assertEqual(
            strings.to_json(np.array([1/3, 2/3, 3/3])),
            '[\n    0.33,\n    0.67,\n    1.0\n]'
        )

        import datetime

        self.assertEqual(
            strings.to_json(datetime.datetime(2018, 4, 22, 12, 00, 35)),
            '"2018/04/22-12:00:35"'
        )

    def test_to_yaml(self):
        self.assertEqual(strings.to_yaml(dict(a=None)), 'a: null\n')
        self.assertEqual(strings.to_yaml(dict()), '{}\n')
        self.assertEqual(strings.to_yaml(
            dict(b=1, a=2)),
            'a: 2\nb: 1\n'
        )

        import datetime

        self.assertEqual(
            strings.to_yaml(dict(a=datetime.datetime(2018, 4, 22, 12, 00, 35))),
            'a: 2018-04-22 12:00:35\n'
        )

