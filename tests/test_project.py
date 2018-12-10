#!/bin/python3
# author: Jan Hybs

import tests


tests.fix_paths()

import os
import unittest
import cihpc.core


project_dir = os.path.join(tests.__dir__, 'project-example')


class TestProject(unittest.TestCase):

    def test_parse_args(self):
        with self.assertRaises(SystemExit):
            cihpc.core.parse_args([])

        args = [
            '--project=foo',
            '--log-path=foo.log',
            '--watch-commit-policy=commit-per-day',
            '--git-commit=foobar',
            '--tty',
        ]
        parsed = cihpc.core.parse_args(args)
        self.assertEqual(parsed.project, 'foo')
        self.assertEqual(parsed.log_path, 'foo.log')
        self.assertEqual(parsed.tty, True)
        self.assertEqual(parsed.watch_commit_policy, 'commit-per-day')
        self.assertEqual(parsed.action.value, 'run')
        self.assertListEqual(parsed.git_commit, ['foobar'])

        # no valid config
        with self.assertRaises(SystemExit):
            cihpc.core.main(args)

        args = [
            '--project=foo',
            '--log-level=warning',
            '--config-dir=%s' % project_dir,
        ]
        cihpc.core.main(args)
