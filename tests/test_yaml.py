#!/bin/python3
# author: Jan Hybs

import tests

import yaml
from unittest import TestCase

from cihpc.cfg.config import global_configuration
from cihpc.utils import extend_yaml

repeat_yaml = '''
foo: !repeat a 5
'''

range_yaml = '''
foo: !range 1 5
bar: !range 1 2 6
'''

sh_yaml = '''
foo: !sh yaml/foo.txt
'''


class TestExtendYaml(TestCase):

    def test_extend(self):
        extend_yaml.extend()
        self.assertIn('!range', yaml.Loader.yaml_constructors)
        self.assertIn('!repeat', yaml.Loader.yaml_constructors)
        self.assertIn('!sh', yaml.Loader.yaml_constructors)

    def test_repeat(self):
        extend_yaml.extend()

        result = yaml.load(repeat_yaml)
        self.assertEqual(result.get('foo'), 'a'*5)

        result = yaml.load(range_yaml)
        self.assertTupleEqual(tuple(result.get('foo')), tuple(range(1, 5)))
        self.assertTupleEqual(tuple(result.get('bar')), tuple(range(1, 2, 6)))

        global_configuration.project_cfg_dir = tests.__dir__

        result = yaml.load(sh_yaml)
        self.assertEqual(result.get('foo'), 'top-secret')

