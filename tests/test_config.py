#!/bin/python3
# author: Jan Hybs

import tests

import random
from os.path import join

from unittest import TestCase
from cfg import cfgutil


project_dir = join(tests.__dir__, 'project-example')
config_path = join(project_dir, 'config.yaml')


class TestConfig(TestCase):

    def test_configure_file(self):

        variables = dict()
        project_configs = list(cfgutil.configure_file(config_path, variables))
        self.assertEqual(len(project_configs), 1)

        variables = cfgutil.load_config(join(project_dir, 'variables-simple.yaml'))
        project_configs = list(cfgutil.configure_file(config_path, variables))
        self.assertEqual(len(project_configs), 1)

        variables = cfgutil.load_config(join(project_dir, 'variables-iter.yaml'))
        project_configs = list(cfgutil.configure_file(config_path, variables))
        self.assertEqual(len(project_configs), 3)

        variables = cfgutil.load_config(join(project_dir, 'variables-complex.yaml'), hostname='foo-bar')
        project_configs = list(cfgutil.configure_file(config_path, variables))
        self.assertEqual(len(project_configs), 1)

        variables = cfgutil.load_config(join(project_dir, 'variables-complex.yaml'), hostname='foo-foo')
        project_configs = list(cfgutil.configure_file(config_path, variables))
        self.assertEqual(len(project_configs), 3)

    def test_configure_string(self):
        variables = dict(
            foo='foo',
            bar=dict(
                foo='123',
                bar=True,
            )
        )
        self.assertEqual(cfgutil.configure_string('<foo>', variables), 'foo')
        self.assertEqual(cfgutil.configure_string('<bar.foo>', variables), '123')
        self.assertEqual(cfgutil.configure_string('<bar.foo|s>', variables), '123')
        self.assertEqual(cfgutil.configure_string('<bar.foo|i>', variables), 123)
        self.assertEqual(cfgutil.configure_string('<bar.foo|f>', variables), 123.0)
        self.assertEqual(cfgutil.configure_string('<bar.bar>', variables), 'True')
        self.assertEqual(cfgutil.configure_string('<bar.bar|b>', variables), True)

        self.assertIsInstance(cfgutil.configure_string('<bar>', variables), str)
        self.assertIsInstance(cfgutil.configure_string('<bar.foo>', variables), str)
        self.assertIsInstance(cfgutil.configure_string('<bar.foo|i>', variables), int)
        self.assertIsInstance(cfgutil.configure_string('<bar.bar|b>', variables), bool)

        variables = dict(
            foo=random.random(),
            bar=dict(
                foo=random.random(),
            )
        )

        config = list(cfgutil.configure_file(config_path, variables))[0]
        self.assertEqual(config['install'][0]['foo'], variables['foo'])
        self.assertEqual(config['install'][0]['bar-foo'], '<bar.foo>')      # is not supported