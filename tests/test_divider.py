#!/bin/python3
# author: Jan Hybs

import tests
from unittest import TestCase
from utils.files.temp_file import divider


class TestDivider(TestCase):

    def test_divider(self):
        value = divider('FOO', '#', '!', '=', 20)
        self.assertEqual(value, '#======= FOO ========!')

        value = divider(None, '?', '^', '.', 20)
        self.assertEqual(value, '?....................^')
