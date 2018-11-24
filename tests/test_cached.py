#!/bin/python3
# author: Jan Hybs

import tests

from unittest import TestCase

from cihpc.cfg.config import global_configuration


class TestCached(TestCase):

    def test_cached(self):
        global_configuration.cache_type = 'TTLCache'
        global_configuration.cache_opts = dict(
            maxsize=10,
            ttl=10 * 60,
        )

        from cihpc.utils.caching import cached

        foo_i = dict(i=0)

        @cached()
        def foo(j):
            foo_i['i'] += 1
            return foo_i['i']

        self.assertEqual(foo(1), 1)
        self.assertEqual(foo(1), 1)
        for i in range(12): foo(i)
        self.assertEqual(foo(1), 13)

        global_configuration.cache_type = None
        bar_i = dict(i=0)

        @cached()
        def bar(j):
            bar_i['i'] += 1
            return bar_i['i']

        self.assertEqual(bar(1), 1)
        self.assertEqual(bar(1), 2)
        for i in range(12): bar(i)
        self.assertEqual(bar(1), 15)