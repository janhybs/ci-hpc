#!/bin/python3
# author: Jan Hybs

import tests


tests.fix_paths()

from unittest import TestCase
from cihpc.core.db import CIHPCMongo


class TestArtifacts_default_configuration(TestCase):

    def test_artifacts_default_configuration(self):
        self.assertEqual(
            CIHPCMongo.artifacts_default_configuration(),
            dict(
                db_name='default',
                col_timers_name='timers',
                col_files_name='files',
                col_history_name='hist',
            )
        )
        self.assertEqual(
            CIHPCMongo.artifacts_default_configuration('foobar'),
            dict(
                db_name='foobar',
                col_timers_name='timers',
                col_files_name='files',
                col_history_name='hist',
            )
        )
