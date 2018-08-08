
from jumpscale import j

JSBASE = j.application.jsbase_get_class()

import sys
import gipc

# def parent(nr=1000):
#     processes = []
#     for i in range(nr):
#         cend, pend = gipc.pipe(duplex=True)  #cend = client end, pend=parent end
#         processes.append((cend, pend ))
#         gipc.start_process(subprocess, (cend,i,))   
#     while True:
#         time.sleep(1)
#         print("############")
#         for proc in processes:
#             cend,pend = proc
#             print(pend.get())


# def subprocess(cend,nr):
#     """
#     """
#     from jumpscale import j
#     cend.put("log: init %s"%nr)
#     try:
#         while True:
#             time.sleep(1)
#             cend.put("alive %s"%nr)
#     except Exception as e:
#         cend.put(e)

# def subprocess2(nr):
#     """
#     """
#     from jumpscale import j
#     import time
#     time.sleep(1)
#     if nr/10==int(nr/10):
#         raise RuntimeError("error")
#     return("test:%s"%nr)

def workers(nr=4):
    # from redis import Redis
    # from rq import Queue

    # q = Queue(connection=Redis())

    # for i in range(100):
    #     job = q.enqueue(subprocess2, i)
    #     # job.perform()
    #     # print (job.result)
    #     # time.sleep(1)
    res=[]
    for i in range(nr):
        res.append(gipc.start_process(worker))
    return res


from rq import Connection, Worker    
from jumpscale import j

def worker():
    """
    """    
    with Connection():
        qs = ['default']
        w = Worker(qs)
        w.work()   
