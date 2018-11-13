#!/bin/python3
# author: Jan Hybs
from multiproc.thread_pool import WorkerPool
import time


def func(worker):
    t = time.time()
    time.sleep(worker.crate)
    return time.time() - t


pool = WorkerPool([1, 2, 2, 1, 1], 2, func)
pool.thread_event.on_enter.on(print)
pool.thread_event.on_exit.on(print)
print(pool.start())
