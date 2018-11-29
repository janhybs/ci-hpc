#!/bin/python3
# author: Jan Hybs


import multiprocessing
from cihpc.core.processing.step_shell import ProcessConfigCrate
from cihpc.common.utils.events import EnterExitEvent


class PoolInt(object):
    def __init__(self, value=0):
        self.value = value

    def __call__(self, *args, **kwargs):
        return self.value


class ActivePool(object):
    def __init__(self):
        super(ActivePool, self).__init__()
        self.mgr = multiprocessing.Manager()
        self.active = self.mgr.list()
        self.lock = multiprocessing.Lock()

    def make_active(self, name):
        with self.lock:
            self.active.append(name)

    def make_inactive(self, name):
        with self.lock:
            self.active.remove(name)

    def __str__(self):
        with self.lock:
            return str(self.active)


def worker(item, process_event, semaphore: multiprocessing.Semaphore, pool, queue, worker, lock):
    from cihpc.core.processing.step_shell import process_popen

    name = multiprocessing.current_process().name

    # -----------------------------------
    semaphore.acquire()
    # -----------------------------------
    pool.make_active(name)
    process_event.on_enter(worker)
    result = process_popen(item)
    queue.put(result.to_json())
    # time.sleep(random.random())
    pool.make_inactive(name)
    # -----------------------------------
    semaphore.release()
    # -----------------------------------


class Worker(multiprocessing.Process):
    def __init__(self, name, crate, process_event, semaphore, pool, lock):
        queue = multiprocessing.Queue()
        self.args = (crate, process_event, semaphore, pool, queue, self, lock)

        self.crate = crate  # type: ProcessConfigCrate
        self.process_event = process_event
        self.pool = pool
        self.semaphore = semaphore
        self.lock = lock
        self.queue = queue

        super(Worker, self).__init__(name=name, target=worker, args=self.args)

    def finish(self):
        self.crate.result = self.queue.get(timeout=5.0)
        self.process_event.on_exit(self)


class WorkerPool(object):
    def __init__(self, items=None, processes=None):
        self.items = items  # type: list[ProcessConfigCrate]
        self.processes = processes or multiprocessing.cpu_count()
        self.semaphore = multiprocessing.Semaphore(self.processes)
        self.pool = ActivePool()
        self.jobs = list()
        self.lock = multiprocessing.Lock()
        self.process_event = EnterExitEvent('process')

        i = 0
        for item in items:
            self.jobs.append(
                Worker(str(i), item, self.process_event, self.semaphore, self.pool, self.lock)
            )
            i += 1

    def start(self):
        for job in self.jobs:
            job.start()

        for job in self.jobs:
            job.join()
            job.finish()
