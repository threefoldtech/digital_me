
from Jumpscale import j
from rq import Queue
import gevent
from redis import Redis
import time

from rq.job import Job

# for the workers RQ
redis_conn = Redis()
workers_queue = Queue(connection=redis_conn)
workers_jobs = {}


def waiter(job):
    while job.result==None:
        time.sleep(0.1)
    return job.result


def job_schedule(method, timeout=60, wait=False, depends_on=None, **kwargs):
    """
    @return job, waiter_greenlet
    """
    job = workers_queue.enqueue_call(func=method, kwargs=kwargs, timeout=timeout, depends_on=depends_on)
    # greenlet = gevent.spawn(waiter, job)
    # job.greenlet = greenlet
    # workers_jobs[job.id] = job
    # if wait:
    #     greenlet.get(block=True, timeout=timeout)
    return job



def testX():
    # import time
    print("!!!!")
    time.sleep(10)
    return(1)
    # return(x)

from toimport import add


# job = job_schedule(testX, timeout=600, wait=False,x=1)

job = workers_queue.enqueue_call(func=add, args=[1,2])

j.shell()