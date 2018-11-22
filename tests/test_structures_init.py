#!/bin/python3
# author: Jan Hybs

from unittest import TestCase

from structures import new, pick


class TestNew(TestCase):

    def test_new(self):
        class A(object):
            def __init__(self, a, b=1, **kwargs):
                self.a = a
                self.b = b

        data = dict(foo=5)
        self.assertEqual(new(data, 'foo', A).a, 5)

        data = dict(foo=dict(a=8))
        self.assertEqual(new(data, 'foo', A).a, 8)
        self.assertEqual(new(data, 'foo', A).b, 1)

        data = dict(foo=dict(a=2, b=5))
        self.assertEqual(new(data, 'foo', A).a, 2)
        self.assertEqual(new(data, 'foo', A).b, 5)

        data = dict(foo=dict())
        self.assertIsNone(new(data, 'bar', A))

        with self.assertRaises(TypeError):
            new(data, 'foo', A)


class TestPick(TestCase):

    def test_pick(self):
        data = dict(a=5, b=6, c=7)
        self.assertEqual(pick(data, None, 'a'), 5)
        self.assertEqual(pick(data, None, 'd', 'b'), 6)
        self.assertEqual(pick(data, 8, 'd', 'e', 'f'), 8)
        self.assertEqual(pick(data, None, 'd'), None)

        # TODO maybe return None or other exception?
        with self.assertRaises(TypeError):
            pick(None, None, 'a')
