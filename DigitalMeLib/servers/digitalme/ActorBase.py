from Jumpscale import j
import gevent

from gevent import queue
from gevent import spawn
import inspect


JSBASE = j.application.jsbase_get_class()

class ActorBase(JSBASE):

    
    def __init__(self,community):
        JSBASE.__init__(self)
        self.community=community
        self.q_in = queue.Queue() 
        self.q_out = queue.Queue() 
        self.task_id_current = 0
        self.greenlet_task = spawn(self._main)
        self.monitors = {}
        
        for method in inspect.getmembers(OptionParser, predicate=inspect.ismethod):
            print("iterate over methods")
            from IPython import embed;embed(colors='Linux')
            s            
            if hasattr(self,"monitor"):
                print("monitor")
                self.greenlet_monitor = spawn(self.monitor)
            else:
                self.greenlet_monitor = None
        if name in self.community.schemas:
            self.schema = self.community.schemas[name]

    def _main(self):
        self.logger.info("%s:mainloop started"%self)
        #make sure communication is only 1 way
        while True:
            task,data=self.q_in.get()
            self.logger.info("%s:TASK:%s:%s"%(self,task,data))
            method = eval("self.%s"%task)
            res = method(data)
            print("main res:%s"%res)
            self.q_out.put([0,res])

    def action_ask(self,name,arg=None):
        cmd = [name,arg]
        self.q_in.put(cmd)
        rc,res = self.q_out.get()
        return rc,res

    def monitor_running(self):
        return self.greenlet_monitor.dead==False

    def running(self):
        return self.greenlet_task.dead==False

    def action_running(self,name):
        from IPython import embed;embed(colors='Linux')
        k

    def data_set(self,data):
        self.data = data

    def data_get(self,data):
        return self.data


    def __str__(self):
        return "actor:%s"%self.name

    __repr__ = __str__