
from jumpscale import j
import os
import sys
from importlib import import_module
JSBASE = j.application.jsbase_get_class()
from gevent import spawn
import gevent

class ActorCommunity(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.servers = {}
        self.actors = {}
        self.actors_dna = {}
        self.schemas = {}

    def start(self):
        gevent.sleep(1000000000000)

    def _key_get(self,name,instance):
        key="%s_%s"%(name.lower().strip(),instance.lower().strip())
        key=key.replace(".","_")
        return key

    @property
    def _path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__))

    def actor_get(self,name,instance,capnp_data=None):
        name=name.lower().strip().replace(".","_")
        key=self._key_get(name,instance)
        if key not in self.actors:
            if name not in self.actors_dna:
                raise RuntimeError("did not find actors dna:%s"%name)
            self.actors[key] = self.actors_dna[name](community=self,name=name,instance=instance)
            if capnp_data is not None:
                self.actors[key].data = self.actors[key].schema.get(capnpbin=capnp_data)          
        return self.actors[key]

    def actor_dna_add(self,path=""):
        """
        @PARAM path can be url or path
        """
        if "http" in path:
            path = j.clients.git.getContentPathFromURLorPath(url)
        if path is "":
            path = "%s/%s"%(self._path, "actors_example")
        
        # tocheck=[]
        for actorpath in  j.sal.fs.listFilesInDir(path, recursive=True, filter="actor_*.py",followSymlinks=True):
            dpath = j.sal.fs.getDirName(actorpath)
            if dpath not in sys.path:
                sys.path.append(dpath)
            self.logger.info("actordna:%s"%actorpath)
            modulename=j.sal.fs.getBaseName(actorpath)[:-3]
            module = import_module(modulename)
            name=modulename[6:]
            self.actors_dna[name]=module.Actor 

            if "SCHEMA" in module.__dict__:  
                schema = self._schema_add(module.SCHEMA,name)                
                self.schemas[name]=schema

    def _schema_add(self,schema,name):
        
        #will check if we didn't define url/name in beginning of schema
        for line in schema.split("\n"):
            if line.strip()=="":
                continue
            if line.startswith("#"):
                continue
            if line.startswith("@"):
                raise RuntimeError("Schema:\n%s\nshould not define name & url at start, will be added automatically.")
            else:
                break
        splitted=[item.strip().lower() for item in name.split("_")]
        if len(splitted)<2:
            raise RuntimeError("unique name for actor needs to be at least 2 parts")

        SCHEMA2="@url = %s\n"% ".".join(splitted)
        SCHEMA2+="@name = %s\n"% "_".join(splitted)
        SCHEMA2+=schema

        res = j.data.schema.schema_add(SCHEMA2)

        return res[0]     


            

            

    def server_add(self,name,server):
        self.servers[name]=server

    def server_start(self):
        #TODO:*1
        started = []
        try:
            for server in self.servers[:]:
                server.start()
                started.append(server)
                name = getattr(server, 'name', None) or server.__class__.__name__ or 'Server'
                self.logger.info('%s started on %s', name, server.address)
        except:
            self.stop(started)
            raise

    def server_stop(self, servers=None):
        if servers is None:
            servers = self.servers[:]
        for server in servers:
            try:
                server.stop()
            except:
                if hasattr(server, 'loop'): # gevent >= 1.0
                    server.loop.handle_error(server.stop, *sys.exc_info())
                else: # gevent <= 0.13
                    import traceback
                    traceback.print_exc()


