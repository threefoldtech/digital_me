from rq import Connection, Worker
from Jumpscale import j



with Connection():
    qs = ['default']
    w = Worker(qs)
    w.work()

