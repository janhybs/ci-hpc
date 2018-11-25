#!/bin/python3
# author: Jan Hybs
import os

import tests

import random
from os.path import join

from unittest import TestCase

from cihpc.utils.datautils import merge_dict


project_dir = join(tests.__dir__, 'project-example')
config_path = join(project_dir, 'config.yaml')


class TestConfig(TestCase):

    def test_configure_file(self):
        from cihpc.cfg import cfgutil

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
        from cihpc.cfg import cfgutil

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

    def test_config_special_variables(self):
        from cihpc.structures.project import Project
        from cihpc.cfg import cfgutil

        project = Project(name='foobar')

        self.assertEqual(
            cfgutil.configure_string('My home is <os.HOME>', project.global_args),
            'My home is %s' % os.environ.get('HOME')
        )
        self.assertEqual(
            cfgutil.configure_string('My home is <$.HOME>', project.global_args),
            'My home is %s' % os.environ.get('HOME')
        )

        kwargs = merge_dict(
            project.global_args,
            foobar=dict(
                foo='foo',
                bar=dict(
                    foo='foo.bar'
                )
            )
        )

        self.assertEqual(
            cfgutil.configure_string('foobar.bar.foo is <foobar.bar.foo> and I am <$.USER>', kwargs),
            'foobar.bar.foo is foo.bar and I am %s' % os.environ.get('USER')
        )
