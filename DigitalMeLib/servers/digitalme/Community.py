
from Jumpscale import j
import os
import sys
from importlib import import_module
JSBASE = j.application.jsbase_get_class()
from gevent import spawn
import gevent

from .Coordinator import Coordinator
from .Service import Service

class Community(JSBASE):
    """
    is a set of coordinators
    """

    def __init__(self):
        JSBASE.__init__(self)

        self.coordinators = {}

        self.coordinator_dna = {}    #are the classes for coordinators
        self.service_dna = {}        #are the classes for services (which can run inside coordinators)
        self.knowledge = []          #are paths to the knowledge to learn

        self._key = None

    def coordinator_class_get(self):
        return Coordinator

    def service_class_get(self):
        return Service        

    def start(self):
        gevent.sleep(1000000000000)

    def coordinator_get(self,name="main",capnp_data=None):
        name = j.core.text.strip_to_ascii_dense(name)
        if name not in self.coordinators:
            if name not in self.coordinator_dna:
                raise RuntimeError("did not find coordinator dna:%s"%name)
            self.actors[key] = self.coordinator_dna[name](community=self,name=name,instance=instance)
            if capnp_data is not None:
                self.actors[key].data = self.actors[key].schema.get(capnpbin=capnp_data)          
        return self.actors[key]

    def error_raise(self,msg,e=None,cat=""):
        msg="ERROR in %s\n"%self
        msg+="msg\n"
        raise j.exceptions.Input(msg,eco=e)


    def knowledge_learn(self,path=""):
        """

        add knowledge to the community, do this by loading service or coordinator classes

        @PARAM path can be git url or path

        """
        if path not in self.knowledge:
            self.knowledge.append(path)
        if "http" in path:
            path = j.clients.git.getContentPathFromURLorPath(url)
        if path is "":
            path = "%s/%s"%(self._path, "actors_example")
        
        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="service_*.py",followSymlinks=True)
        tocheck += j.sal.fs.listFilesInDir(path, recursive=True, filter="coordinator_*.py",followSymlinks=True) 
        
        for classpath in  tocheck:
            dpath = j.sal.fs.getDirName(classpath)
            if dpath not in sys.path:
                sys.path.append(dpath)
            self.logger.info("dna:%s"%classpath)
            modulename=j.sal.fs.getBaseName(classpath)[:-3]

            try:
                self.logger.info("import module:%s"%modulename)
                module = import_module(modulename)
                self.logger.debug("ok")
            except Exception as e:
                self.error_raise("could not import module:%s"%modulename,e)

            
            if modulename.startswith("service_"):
                name = modulename[8:]
                self.coordinator_dna[name] = self._module_fix(module,name,"service")
            else:
                name = modulename[12:]
                self.service_dna[name] = self._module_fix(module,name,"coordinator")

    def knowledge_refresh(self):
        """
        reload all  service or coordinator classes in existing paths
        """
        for path in self.knowledge:
            self.learn(path)

    def _module_fix(self,module,name,cat):
        
        if not "SCHEMA" in module.__dict__:  
            raise RuntimeError("could not find SCHEMA in module:%s"%module)     
            
        name = j.core.text.strip_to_ascii_dense(name)
        
        #will check if we didn't define url/name in beginning of schema
        schema1=""
        for line in module.SCHEMA.split("\n"):
            if line.strip()=="":
                continue
            if line.startswith("#"):
                continue
            if line.startswith("@"):
                raise RuntimeError("Schema:\n%s\nshould not define name & url at start, will be added automatically."%name)
            schema1+="%s\n"%line
            
        splitted=[item.strip().lower() for item in name.split("_")]
        if len(splitted)<2:
            raise RuntimeError("unique name for actor needs to be at least 2 parts separated with .Now:%s"%name)

        SCHEMA2="@url = %s.%s\n"% (cat,".".join(splitted))
        SCHEMA2+="@name = %s\n"% "_".join(splitted)
        SCHEMA2+=schema1

        try:
            module.schema_obj = j.data.schema.schema_add(SCHEMA2)
        except Exception as e:
            self.error_raise("cannot parse schema:%s"%SCHEMA2,e=e)

        return module    
            

    # def server_add(self,name,server):
    #     self.servers[name]=server

    # def server_start(self):
    #     started = []
    #     try:
    #         for server in self.servers[:]:
    #             server.start()
    #             started.append(server)
    #             name = getattr(server, 'name', None) or server.__class__.__name__ or 'Server'
    #             self.logger.info('%s started on %s', name, server.address)
    #     except:
    #         self.stop(started)
    #         raise

    # def server_stop(self, servers=None):
    #     if servers is None:
    #         servers = self.servers[:]
    #     for server in servers:
    #         try:
    #             server.stop()
    #         except:
    #             if hasattr(server, 'loop'): # gevent >= 1.0
    #                 server.loop.handle_error(server.stop, *sys.exc_info())
    #             else: # gevent <= 0.13
    #                 import traceback
    #                 traceback.print_exc()


