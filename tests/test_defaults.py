#!/bin/python3
# author: Jan Hybs

import tests
from unittest import TestCase
from defaults import aggregation_default_configuration, artifacts_default_configuration


class TestAggregation_default_configuration(TestCase):
    def test_aggregation_default_configuration(self):
        self.assertEqual(
            aggregation_default_configuration(),
            [
                {
                    '$unwind': '$libs',
                },
                {
                    '$unwind': '$timers',
                }
            ]
        )
        self.assertEqual(
            aggregation_default_configuration('foobar'),
            [
                {'$unwind': '$libs'},
                {'$unwind': '$timers'},
            ]
        )


class TestArtifacts_default_configuration(TestCase):
    def test_artifacts_default_configuration(self):
        self.assertEqual(
            artifacts_default_configuration(),
            dict(
                db_name='default',
                col_timers_name='timers',
                col_files_name='files',
                col_history_name='hist',
            )
        )
        self.assertEqual(
            artifacts_default_configuration('foobar'),
            dict(
                db_name='foobar',
                col_timers_name='timers',
                col_files_name='files',
                col_history_name='hist',
            )
        )
