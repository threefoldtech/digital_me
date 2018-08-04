from jumpscale import j
import gevent
JSBASE = j.servers.gworld.actor_class_get()

SCHEMA = """
llist2 = "" (LS) #L means = list, S=String        
nr = 4
date_start = 0 (D)
description = ""
token_price = "10 USD" (N)
cost_estimate:hw_cost = 0.0 #this is a comment
"""

class Actor(JSBASE):

    # def __init__(self,community,name,instance):
    #     JSBASE.__init__(self,community=community,name=name,instance=instance)


    def task1(self,id):
        print("TASK1:%s"%self)
        return id+1

    def task2(self,id):
        return "task2:%s"%id

    def monitor(self):
        print("monitor started")
        counter = 0
        while True:
            gevent.sleep(1)
            counter+=5
            print("monitor:%s:%s"%(self,counter))

    def ok(self):
        pass