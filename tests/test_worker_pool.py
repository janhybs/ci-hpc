#!/bin/python3
# author: Jan Hybs

import tests


tests.fix_paths()

from loguru import logger
import time




import multiprocessing
from unittest import TestCase
from cihpc.common.processing.pool import (
    WorkerPool,
    Worker,
    LogStatusFormat,
)


cpu_count = multiprocessing.cpu_count()


class TestWorkerPool(TestCase):

    def test_start_serial(self):

        cpu_count = 1
        counter = dict(cnt=0)

        def func(worker: Worker):
            counter['cnt'] += 1
            return [counter['cnt'], worker.crate['foo']]

        items = [dict(foo=123), dict(foo=456)]
        threads = [Worker(crate=x, target=func) for x in items]

        pool = WorkerPool(cpu_count=cpu_count, threads=threads)
        pool.start_serial()
        self.assertListEqual(pool.result, [[1, 123], [2, 456]])

    def test_start_parallel(self):
        class A:
            def __init__(self, name):
                self.name = name

        items = [
            A(name='a'), A(name='b'), A(name='c'),
            A(name='a'), A(name='b'), A(name='c'),
            A(name='a'), A(name='b'), A(name='c'),
        ]
        result = [[i + 1, items[i].name] for i in range(len(items))]

        def func(worker: Worker):
            counter['cnt'] += 1
            time.sleep(0.001)
            return [counter['cnt'], worker.crate.name]

        # this test is not by its nature bulletproof
        # TODO make parallel testing more robust
        if cpu_count > 1:
            with self.assertRaises(AssertionError):
                for i in range(25):
                    threads = [Worker(crate=x, target=func) for x in items]
                    counter = dict(cnt=0)
                    pool = WorkerPool(cpu_count=2, threads=threads)
                    pool.log_statuses(format=LogStatusFormat.ONELINE_GROUPED)
                    pool.start_parallel()
                    self.assertListEqual(pool.result, result)

        for i in range(10):
            threads = [Worker(crate=x, target=func) for x in items]
            counter = dict(cnt=0)
            pool = WorkerPool(cpu_count=2, threads=threads)
            pool.log_statuses(format=LogStatusFormat.COMPLEX)
            pool.start_serial()
            self.assertListEqual(pool.result, result)

        for i in range(10):
            threads = [Worker(crate=x, target=func) for x in items]
            counter = dict(cnt=0)
            pool = WorkerPool(cpu_count=1, threads=threads)
            pool.log_statuses(format=LogStatusFormat.SIMPLE)
            pool.start_serial()
            self.assertListEqual(pool.result, result)

        for i in range(10):
            threads = [Worker(crate=x, target=func) for x in items]
            counter = dict(cnt=0)
            pool = WorkerPool(cpu_count=1, threads=threads)
            pool.log_statuses(format=LogStatusFormat.ONELINE)
            pool.start()
            self.assertListEqual(pool.result, result)
