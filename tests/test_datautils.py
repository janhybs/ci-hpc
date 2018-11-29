#!/bin/python3
# author: Jan Hybs

import tests

from unittest import TestCase
from cihpc.common.utils.datautils import (
    recursive_get,
)


class TestRecursive_get(TestCase):

    def test_recursive_get(self):
        data = dict(foo=dict(bar=5))
        self.assertEqual(recursive_get(data, 'foo'), dict(bar=5))
        self.assertEqual(recursive_get(data, 'foo'), dict(bar=5))

        self.assertEqual(recursive_get(data, 'foo.bar'), 5)
        self.assertEqual(recursive_get(data, 'bar.foo', True), True)
        self.assertEqual(recursive_get(data, 'bar|foo', 42, '|'), 42)
        self.assertEqual(recursive_get(data, 'foo|foo', 42, '|'), 42)
        self.assertEqual(recursive_get(data, 'foo|bar', 42, '|'), 5)

        self.assertEqual(recursive_get(None, None), None)
        self.assertEqual(recursive_get('', ''), None)
        self.assertEqual(recursive_get(dict(), None), None)
        self.assertEqual(recursive_get(dict(), None, False), False)
#
# class TestFlatten(TestCase):
#     def test_flatten(self):
#         self.fail()
#
#
# class TestIter_over(TestCase):
#     def test_iter_over(self):
#         self.fail()
#
#
# class TestMerge_dict(TestCase):
#     def test_merge_dict(self):
#         self.fail()
#
#
# class TestXdict(TestCase):
#     pass
#
#
# class TestJoin_lists(TestCase):
#     def test_join_lists(self):
#         self.fail()
#
#
# class TestFilter_keys(TestCase):
#     def test_filter_keys(self):
#         self.fail()
#
#
# class TestFilter_values(TestCase):
#     def test_filter_values(self):
#         self.fail()
