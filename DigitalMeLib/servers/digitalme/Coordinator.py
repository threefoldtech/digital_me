from jumpscale import j
from .ActorBase import ActorBase



class Coordinator(ActorBase):

    
    def __init__(self,community,name):
        ActorBase.__init__(community=community)
        self.data.name = name
        self.init()

    @property
    def name(self):
        return self.data.name

    @property
    def key(self):
        if self._key == None:
            self._key = "%s"%(j.data.text.strip_to_ascii_dense(self.name))
        return self._key


    def __str__(self):
        return "coordinator:%s"%self.name
