#!/bin/python3
# author: Jan Hybs

import tests

from os.path import join

from unittest import TestCase
from cihpc.main import parse_args, main

project_dir = join(tests.__dir__, 'project-example')


class TestProject(TestCase):

    def test_parse_args(self):
        with self.assertRaises(SystemExit):
            parse_args([])

        args = [
            '--project=foo',
            '--log-path=foo.log',
            '--watch-commit-policy=commit-per-day',
            '--git-commit=foobar',
            '--tty',
        ]
        parsed = parse_args(args)
        self.assertEqual(parsed.project, 'foo')
        self.assertEqual(parsed.log_path, 'foo.log')
        self.assertEqual(parsed.tty, True)
        self.assertEqual(parsed.watch_commit_policy, 'commit-per-day')
        self.assertListEqual(parsed.step, ['install', 'test'])
        self.assertListEqual(parsed.git_commit, ['foobar'])

        # no valid config
        with self.assertRaises(SystemExit):
            main(args)

        args = [
            '--project=foo',
            '--log-level=warning',
            '--config-dir=%s' % project_dir,
        ]
        main(args)