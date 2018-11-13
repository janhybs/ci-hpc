#!/bin/python3
# author: Jan Hybs

import multiprocessing
import threading
import time

from multiproc.complex_semaphore import ComplexSemaphore
from proc.step.step_shell import ProcessConfigCrate
from utils.events import EnterExitEvent


class PoolInt(object):
    def __init__(self, value=0):
        self.value = value

    def __call__(self, *args, **kwargs):
        return self.value


class Worker(threading.Thread):
    def __init__(self, crate, semaphore, thread_event, target, cpus=1):
        super(Worker, self).__init__()
        self.cpus = cpus                    # type: int
        self.semaphore = semaphore          # type: ComplexSemaphore
        self.thread_event = thread_event    # type: EnterExitEvent
        self.target = target                # type: callable
        self.crate = crate                  # type: ProcessConfigCrate
        self.result = None
        self.cpus = cpus
        self.status = 'waiting'

    def run(self):
        self.semaphore.acquire(value=self.cpus)
        self.status = 'running'
        self.thread_event.on_enter(self)

        self.result = self.target(self)

        self.status = 'finished'
        self.semaphore.release(value=self.cpus)

    def __repr__(self):
        return '{self.name}({self.cpus}x, , [{self.status}])'.format(self=self)


class WorkerPool(object):
    def __init__(self, items, processes, target):
        self.items = items
        self.processes = processes or multiprocessing.cpu_count()
        self.semaphore = ComplexSemaphore(self.processes)
        self.thread_event = EnterExitEvent('thread')
        self.threads = list()

        for item in items:
            self.threads.append(
                Worker(
                    crate=item,
                    semaphore=self.semaphore,
                    thread_event=self.thread_event,
                    target=target
                )
            )

    def update_cpu_values(self, target):
        for thread in self.threads:
            thread.cpus = target(thread)

    @property
    def result(self):
        return [thread.result for thread in self.threads]

    def start_serial(self):
        for thread in self.threads:
            thread.start()
            thread.join()
            self.thread_event.on_exit(thread)

    def start_parallel(self):
        for thread in self.threads:
            thread.start()

        for thread in self.threads:
            thread.join()
            self.thread_event.on_exit(thread)

        return self.result