from Jumpscale import j
from .ActorBase import ActorBase

class Service(ActorBase):
    
    def __init__(self,community,name,instance,data):
        data.name = name
        data.instance = instance
        self.__key = None
        ActorBase.__init__(self, community=community, data=data)
        self.init()

    def init(self):
        pass

    @property
    def _name(self):
        return self.data.name

    @property
    def _instance(self):
        return self.data.instance

    @property
    def _key(self):
        if self.__key == None:
            self.__key ="%s_%s"%(j.core.text.strip_to_ascii_dense(self.name),j.core.text.strip_to_ascii_dense(self.instance))
        return self.__key


    def __str__(self):
        return "service:%s:%s"%(self._name,self._instance)
