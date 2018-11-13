#!/bin/python3
# author: Jan Hybs


import multiprocessing
from proc.step.step_shell import ProcessConfigCrate
from utils.events import EnterExitEvent


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
    from proc.step.step_shell import process_popen

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

#
# if __name__ == '__main__':
#     pool = ActivePool()
#     s = multiprocessing.Semaphore(3)
#     jobs = [
#         multiprocessing.Process(target=worker, name=str(i), args=(s, pool))
#         for i in range(10)
#         ]
#
#     for j in jobs:
#         j.start()
#
#     for j in jobs:
#         j.join()
#         print('Now running: %s' % str(pool))
#
# #
# import multiprocessing
# import time
#
#
#
# # class Worker(multiprocessing.Process):
# #     def __init__(self, shellpath=None):
# #         super(Worker, self).__init__()
# #         self.shellpath = shellpath
# #         self.free = True
# #         print(self, 'created')
# #
# #     def run(self):
# #         self.free = False
# #         print(self, 'running')
# #
# #         time.sleep(1)
# #
# #         print(self, 'done')
# #         self.free = True
# #
# #     def __repr__(self):
# #         return super(Worker, self).__repr__() + ' [%s]' % self.free
#
#
# class WorkerPool(object):
#     """
#     :type items:    list[proc.step.step_shell.ProcessConfigCrate]
#     :type pool:     ThreadPool
#     """
#
#     def __init__(self, items=None, processes=None):
#         from multiprocessing.pool import ThreadPool
#
#         self.event = multiprocessing.Event()
#         self.pool = ThreadPool(processes or multiprocessing.cpu_count())
#         for item in items:
#             item.event = self.event
#         self.items = items
#
#     def start(self):
#         from proc.step.step_shell import process_popen
#         result = self.pool.map(process_popen, self.items)
#         print(result)
#
# #
# # def f(x):
# #     print(x)
# #     time.sleep(.5)
# #     return x*x
# #
# #
# # items = [
# #     ['/home/jan-hybs/projects/ci-hpc/projects/hello-world/tmp.hello-world/2.test/1.testing-phase/rep-1-3/var-1-2/cfg-1-3/shell.sh', 'log+stdout'],
# #     ['/home/jan-hybs/projects/ci-hpc/projects/hello-world/tmp.hello-world/2.test/1.testing-phase/rep-1-3/var-1-2/cfg-2-3/shell.sh', 'log+stdout'],
# #     ['/home/jan-hybs/projects/ci-hpc/projects/hello-world/tmp.hello-world/2.test/1.testing-phase/rep-1-3/var-1-2/cfg-3-3/shell.sh', 'log+stdout'],
# # ]
# #
# # if __name__ == '__main__':
# #     # pool = Pool(processes=1)              # start 4 worker processes
# #     # result = pool.apply_async(f, [10])    # evaluate "f(10)" asynchronously
# #     # print(result.get(timeout=1))           # prints "100" unless your computer is *very* slow
# #     # print(pool.map(f, range(10)))          # prints "[0, 1, 4,..., 81]"
# #
# #     pool = WorkerPool(items)
# #     pool.start()
# #     print(pool)
