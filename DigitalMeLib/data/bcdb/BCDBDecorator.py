
from gevent.event import Event
from Jumpscale import j

#will make sure that every decorated method get's execute one after the other


def queue_method(func):
    def wrapper_queue_method(*args, **kwargs):
        if "noqueue" in kwargs:
            kwargs.pop("noqueue")
            res = func(*args,**kwargs)
            return res
        else:
            event=Event()
            self=args[0]
            # self.logger.debug(str(func))
            j.data.bcdb.latest.queue.put((func,args,kwargs, event,None))
            event.wait(100.0) #will wait for processing
            return
    return wrapper_queue_method

def queue_method_results(func):
    def wrapper_queue_method(*args, **kwargs):
        if "noqueue" in kwargs:
            kwargs.pop("noqueue")
            res = func(*args,**kwargs)
            return res
        else:
            event=Event()
            self=args[0]
            id = j.data.bcdb.latest.results_id+1  #+1 makes we have copy
            if id == 100000:
                id = 0
                self.results_id = 0
            j.data.bcdb.latest.results_id+=1
            # self.logger.debug(str(func))
            j.data.bcdb.latest.queue.put((func,args,kwargs, event,id))
            event.wait(100.0) #will wait for processing
            res = j.data.bcdb.latest.results[id]
            j.data.bcdb.latest.results.pop(id)
            return res
    return wrapper_queue_method
