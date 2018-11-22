#!/bin/python3
# author: Jan Hybs

import tests
from unittest import TestCase
from processing.multi_processing.complex_semaphore import ComplexSemaphore


class TestComplexSemaphore(TestCase):
    def test_enter_exit(self):
        semaphore = ComplexSemaphore(10)

        self.assertEqual(semaphore.value, 10)
        self.assertEqual(semaphore.limit, 10)

        with semaphore:
            self.assertEqual(semaphore.value, 9)
            self.assertEqual(semaphore.limit, 10)

        self.assertEqual(semaphore.value, 10)
        self.assertEqual(semaphore.limit, 10)

    def test_acquire(self):
        semaphore = ComplexSemaphore(10)

        semaphore.acquire(value=1)
        self.assertEqual(semaphore.value, 10 - 1)
        semaphore.release(value=1)
        self.assertEqual(semaphore.value, 10)

        semaphore.acquire(value=5)
        self.assertEqual(semaphore.value, 10 - 5)
        semaphore.release(value=5)
        self.assertEqual(semaphore.value, 10)

        with self.assertRaises(ValueError):
            semaphore.acquire(value=11)

    def test_release(self):
        semaphore = ComplexSemaphore(10)

        semaphore.acquire(value=1)
        self.assertEqual(semaphore.value, 10 - 1)
        semaphore.release(value=1)
        self.assertEqual(semaphore.value, 10)

        semaphore.acquire(value=5)
        self.assertEqual(semaphore.value, 10 - 5)
        semaphore.release(value=3)
        self.assertEqual(semaphore.value, 8)
