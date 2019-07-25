#!/bin/python3
# author: Jan Hybs
import cihpc.core.parsers
import tests
from cihpc.core import ArgAction


tests.fix_paths()

import os
import unittest
import cihpc.core


project_dir = os.path.join(tests.__dir__, 'project-example')


class TestProject(unittest.TestCase):

    def test_parse_args(self):
        with self.assertRaises(SystemExit):
            cihpc.core.parsers.parse_args(['--log-level=foo'])

        args = [
            '--config-dir=/foo/' + project_dir,
            '--log-path=foo.log',
            '--watch-commit-policy=commit-per-day',
            '--git-commit=foobar',
            '--tty',
        ]
        parsed = cihpc.core.parsers.parse_args(args)
        self.assertEqual(parsed.log_path, 'foo.log')
        self.assertEqual(parsed.tty, True)
        self.assertEqual(parsed.watch_commit_policy, 'commit-per-day')
        self.assertIs(parsed.action.enum, ArgAction.Values.RUN)
        self.assertListEqual(parsed.git_commit, ['foobar'])

        # no valid config
        with self.assertRaises(SystemExit):
            cihpc.core.main(args)

        args = [
            '--log-level=warning',
            '--config-dir=%s' % project_dir,
        ]
        cihpc.core.main(args)
