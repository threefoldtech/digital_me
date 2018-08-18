from jumpscale import j
from .ActorBase import ActorBase



class Coordinator(ActorBase):

    
    def __init__(self,community,name,data):
        data.name = name
        ActorBase.__init__(self,community=community,data=data)
        self.services = {}
        self.services_allowed = ["*"]
        self.init()

    def init(self):
        pass

    def service_get(self,name,instance="main",capnp_data=None):
        name = j.data.text.strip_to_ascii_dense(name)
        if not "*" in self.services_allowed and not name in self.services_allowed:
            raise RuntimeError("service:%s not allowed in coordinator:%s"%(name,self))
        instance = j.data.text.strip_to_ascii_dense(instance)
        key="%s_%s"%(name,instance)
        if key not in self.services:
            if name not in self.community.service_dna:
                raise RuntimeError("did not find service dna:%s"%name)
            schema_obj = self.community.service_dna[name].schema_obj
            if capnp_data is not None:
                data = schema_obj.get(capnpbin=capnp_data)
            else:
                data = schema_obj.new()
            self.services[key] = self.community.service_dna[name].Service(community=self,name=name,instance=instance,data=data)

        return self.services[key]

    def _service_action_ask(self,instance,name):
        cmd = [name,arg]
        self.q_in.put(cmd)
        rc,res = self.q_out.get()
        return rc,res

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
