#!/bin/python3
# author: Jan Hybs

import tests

import time

import cihpc.utils.logging
cihpc.utils.logging.logger.set_level('WARNING')


import multiprocessing
from unittest import TestCase
from cihpc.processing.multi_processing.thread_pool import (
    WorkerPool, Worker, LogStatusFormat
)


cpu_count = multiprocessing.cpu_count()


class TestWorkerPool(TestCase):

    def test_start_serial(self):
        cihpc.utils.logging.logger.set_level('WARNING')

        items = [dict(foo=123), dict(foo=456)]
        processes = 1

        counter = dict(cnt=0)

        def func(worker: Worker):
            counter['cnt'] += 1
            return [counter['cnt'], worker.crate['foo']]

        pool = WorkerPool(items, processes, func)
        pool.start_serial()
        self.assertListEqual(pool.result, [[1, 123], [2, 456]])

    def test_start_parallel(self):
        cihpc.utils.logging.logger.set_level('WARNING')

        class A:
            def __init__(self, name):
                self.name = name

        items = [
            A(name='a'), A(name='b'), A(name='c'),
            A(name='a'), A(name='b'), A(name='c'),
            A(name='a'), A(name='b'), A(name='c'),
        ]
        result = [[i+1, items[i].name] for i in range(len(items))]

        def func(worker: Worker):
            counter['cnt'] += 1
            time.sleep(0.001)
            return [counter['cnt'], worker.crate.name]

        # this test is not by its nature bulletproof
        # TODO make parallel testing more robust
        if cpu_count > 1:
            with self.assertRaises(AssertionError):
                for i in range(25):
                    counter = dict(cnt=0)

                    pool = WorkerPool(items, 2, func)
                    pool.log_statuses(format=LogStatusFormat.ONELINE_GROUPED)
                    pool.start_parallel()
                    self.assertListEqual(pool.result, result)

        for i in range(10):
            counter = dict(cnt=0)
            pool = WorkerPool(items, 2, func)
            pool.log_statuses(format=LogStatusFormat.COMPLEX)
            pool.start_serial()
            self.assertListEqual(pool.result, result)

        for i in range(10):
            counter = dict(cnt=0)
            pool = WorkerPool(items, 1, func)
            pool.log_statuses(format=LogStatusFormat.SIMPLE)
            pool.start_serial()
            self.assertListEqual(pool.result, result)

        for i in range(10):
            counter = dict(cnt=0)
            pool = WorkerPool(items, 1, func)
            pool.log_statuses(format=LogStatusFormat.ONELINE)
            pool.start_parallel()
            self.assertListEqual(pool.result, result)
