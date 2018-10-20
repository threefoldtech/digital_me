import sys
import os
from Jumpscale import j
from gevent.pool import Pool
from gevent import time,signal
import gevent
from gevent.server import StreamServer
from .handlers import Handler
from .GedisChatBot import GedisChatBotFactory
from .GedisCmds import GedisCmds

JSConfigBase = j.tools.configmanager.JSBaseClassConfig



TEMPLATE = """
    host = "0.0.0.0"
    port = "9900"
    ssl = false
    adminsecret_ = ""
    """

def waiter(job):
    while job.result==None:
        time.sleep(0.1)
    return job.result


class GedisServer(StreamServer, JSConfigBase):
    def __init__(self, instance, data=None, parent=None, interactive=False, template=None):
        if data is None:
            data = {}
        JSConfigBase.__init__(self, instance=instance, data=data, parent=parent, template=template or TEMPLATE, interactive=interactive)

        self._sig_handler = []

        self.cmds_meta = {}  #is the metadata of the actor
        self.classes = {}  #the code as set by the gediscmds class = actor cmds
        self.schema_urls = []  #used at python client side

        # self.static_files = {}

        # self.cmds = {}  #will be dynamically loaded while the server is being used

        # self.serializer = None

        self.ssl_priv_key_path = None
        self.ssl_cert_path = None

        self.host = self.config.data["host"]
        self.port = int(self.config.data["port"])
        self.address = '{}:{}'.format(self.host, self.port)
        self.ssl = self.config.data["ssl"]

        self.web_client_code = None
        self.code_generated_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "gedis", self.instance, "server")

        self.chatbot = GedisChatBotFactory(ws=self)

        self.namespaces = ["system","default"]

        self.logger_enable()


        # hook to allow external servers to find this gedis
        j.servers.gedis.latest = self

        # create dirs for generated codes and make sure is empty
        for cat in ["server", "client"]:
            code_generated_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "gedis", self.instance, cat)
            j.sal.fs.remove(code_generated_dir)
            j.sal.fs.createDir(code_generated_dir)
            j.sal.fs.touch(j.sal.fs.joinPaths(code_generated_dir, '__init__.py'))

        # now add the one for the server
        if self.code_generated_dir not in sys.path:
            sys.path.append(self.code_generated_dir)

        self.actors_add(namespace="system",path = "%s/systemactors" % j.servers.gedis.path)  # add the system actors


        self._sig_handler.append(gevent.signal(signal.SIGINT, self.stop))

        # from gevent import monkey
        # monkey.patch_thread() #TODO:*1 dirty hack, need to use gevent primitives, suggest to add flask server
        # import threading
        self.handler = Handler(self)
        if self.ssl:
            self.ssl_priv_key_path, self.ssl_cert_path = self.sslkeys_generate()
            # Server always supports SSL
            # client can use to talk to it in SSL or not
            self.redis_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=self.handler.handle_redis,
                keyfile=self.ssl_priv_key_path,
                certfile=self.ssl_cert_path
            )
        else:
            self.redis_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=self.handler.handle_redis
            )


    #######################################CODE GENERATION

    def code_generate_last_step(self):
        # generate web client
        commands = []
        for key,cmds_ in self.cmds_meta.items():
            # if 'model_' in key:
            #     continue
            commands.append(cmds_)
        self.code_js_client = j.tools.jinja2.file_render("%s/templates/client.js" % j.servers.gedis.path,
                                                         commands=commands,write=False)

    ########################POPULATION OF SERVER#########################

    def models_add(self, models, namespace="default"):
        """
        :param models:  e.g. bcdb.models.values() or bcdb itself
        :param namespace:
        :return:
        """
        if namespace not in self.namespaces:
            self.namespaces.append(namespace)
        reset=True
        if not j.data.types.list.check(models):
            if hasattr(models,"models"):
                models=models.models.values()
        for model in models:
            self.logger.info("generate model: model_%s.py" % namespace)
            dest = j.sal.fs.joinPaths(self.code_generated_dir, "model_%s_%s.py" % (namespace,model.key))
            if reset or not j.sal.fs.exists(dest):
                # find_args = ''.join(["{0}={1},".format(p.name, p.default_as_python_code) for p in table.schema.properties if p.index]).strip(',')
                # kwargs = ''.join(["{0}={0},".format(p.name, p.name) for p in table.schema.properties if p.index]).strip(',')
                j.tools.jinja2.file_render("%s/templates/actor_model_server.py"%(j.servers.gedis.path),
                                                    dest=dest,bcdb=model.bcdb,
                                                    schema=model.schema,model=model)

                # self.logger.debug("cmds generated add:%s" % item)
                self.actor_add(namespace=namespace, path=dest)
            self.schema_urls.append(model.schema.url)


    def actors_add(self, path, namespace="default"):
        """
        add commands from 1 actor (or other python) file

        :param name:  each set of cmds need to have a unique name
        :param path: of the actor file
        :return:
        """
        if not j.sal.fs.isDir(path):
            raise RuntimeError
        files = j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py")
        for path2 in files:
            basepath = j.sal.fs.getBaseName(path2)
            if not "__" in basepath and not basepath.startswith("test"):
                # name2 = "%s_%s"%(name,j.sal.fs.getBaseName(path2)[:-3])
                self.actor_add(path2,namespace=namespace)


    def actor_add(self, path ,namespace="default"):
        """
        add commands from 1 actor (or other python) file

        :param name:  each set of cmds need to have a unique name
        :param path: of the actor file
        :return:
        """
        if namespace not in self.namespaces:
            self.namespaces.append(namespace)
        if not j.sal.fs.exists(path):
            raise RuntimeError("cannot find actor:%s"%path)
        self.logger.debug("actor_add:%s:%s"%(namespace,path))
        name = j.sal.fs.getBaseName(path)[:-3]
        if namespace in name and name.startswith("model"):
            name="model_%s"%name.split(namespace, 1)[1].strip("_")
        key="%s__%s"%(namespace,name)
        self.cmds_meta[key]=GedisCmds(server=self, path=path, name=name, namespace=namespace)


    ####################################################################

    def actors_get(self,namespace="default"):
        res=[]
        for key,cmds in self.cmds_meta.items():
            if key.startswith("%s__"%namespace):
                res.append(cmds)
        return res

    def actors_methods_get(self, namespace="default"):
        actors = self.actors_get(namespace)
        res={}
        for actor in actors:
            res[actor.name]={}
            res[actor.name]["schema"]=str(actor.schema)
            res[actor.name]["cmds"] = {}
            for cmdkey,cmd in actor.cmds.items():
                res[actor.name]["cmds"][cmd.name]=str(cmd.args)
        return res


    ##########################CLIENT FROM SERVER #######################

    def client_get(self,namespace="default"):
    
        data ={}
        data["host"] = self.config.data["host"]
        data["port"] = self.config.data["port"]
        data["adminsecret_"] = self.config.data["adminsecret_"]
        data["ssl"] = self.config.data["ssl"]
        data["namespace"] = namespace
        
        return j.clients.gedis.get(instance=self.instance, data=data, reset=False,configureonly=False)

    def client_configure(self,namespace="default"):

        data = {}
        data["host"] = self.config.data["host"]
        data["port"] = self.config.data["port"]
        data["adminsecret_"] = self.config.data["adminsecret_"]
        data["ssl"] = self.config.data["ssl"]
        data["namespace"] = namespace

        return j.clients.gedis.get(instance=self.instance, data=data, reset=False, configureonly=True)

    #######################PROCESSING OF CMDS ##############

    def job_schedule(self,method,  timeout=60,wait=False,depends_on=None, **kwargs):
        """
        @return job, waiter_greenlet
        """
        job = self.workers_queue.enqueue_call(func=method, kwargs=kwargs, timeout=timeout,depends_on=depends_on)
        greenlet = gevent.spawn(waiter, job)
        job.greenlet=greenlet
        self.workers_jobs[job.id]=job
        if wait:
            greenlet.get(block=True, timeout=timeout)
        return job


    def sslkeys_generate(self):
        if self.ssl:
            path = os.path.dirname(self.code_generated_dir)
            res = j.sal.ssl.ca_cert_generate(path)
            if res:
                self.logger.info("generated sslkeys for gedis in %s" % path)
            else:
                self.logger.info('using existing key and cerificate for gedis @ %s' % path)
            key = j.sal.fs.joinPaths(path, 'ca.key')
            cert = j.sal.fs.joinPaths(path, 'ca.crt')
            return key, cert



    def start(self):
        """
        this method is only used when not used in digitalme
        """
        self.code_generate_last_step()

        #WHEN USED OVER WEB, USE THE DIGITALME FRAMEWORK
        # t = threading.Thread(target=self.websocket_server.serve_forever)
        # t.setDaemon(True)
        # t.start()
        # self.logger.info("start Server on {0} - PORT: {1} - WEBSOCKETS PORT: {2}".format(self.host, self.port, self.websockets_port))

        # j.shell()
        print("RUNNING")
        print(self)
        self.redis_server.serve_forever()

    # def gevent_websocket_server_get():
    #     self.websocket_server = pywsgi.WSGIServer(('0.0.0.0', 9999), self.websocketapp, handler_class=WebSocketHandler)

        # self.websocket_server = self.jsapi_server.websocket_server  #is the server we can use
        # self.jsapi_server.code_js_client = self.code_js_client
        # self.jsapi_server.instance = self.instance
        # self.jsapi_server.cmds = self.cmds
        # self.jsapi_server.classes = self.classes
        # self.jsapi_server.cmds_meta = self.cmds_meta




    def stop(self):
        """
        stop receiving requests and close the server
        """
        # prevent the signal handler to be called again if
        # more signal are received
        for h in self._sig_handler:
            h.cancel()

        self.logger.info('stopping server')
        self.redis_server.stop()


    def __repr__(self):
        return '<Gedis Server address=%s  generated_code_dir=%s)' % (
        self.address, self.code_generated_dir)


    __str__ = __repr__


