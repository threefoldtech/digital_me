from jumpscale import j
from .ActorBase import ActorBase

class Service(ActorBase):
    
    def __init__(self,community,name,instance):
        ActorBase.__init__(community=community)
        self.data.instance = instance
        self.data.name = name
        self.init()

    @property
    def name(self):
        return self.data.name

    @property
    def instance(self):
        return self.data.instance

    @property
    def key(self):
        if self._key == None:
            self._key ="%s_%s"%(j.data.text.strip_to_ascii_dense(self.name),j.data.text.strip_to_ascii_dense(self.instance))
        return self._key


    def __str__(self):
        return "service:%s:%s"%(self.name,self.instance)
