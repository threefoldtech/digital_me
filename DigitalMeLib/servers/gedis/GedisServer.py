import sys
import os
from Jumpscale import j
from gevent.pool import Pool
from gevent import time,signal
import gevent
from gevent.server import StreamServer
from .handlers import RedisRequestHandler
from .GedisChatBot import GedisChatBotFactory
from .GedisCmds import GedisCmds

JSConfigBase = j.tools.configmanager.JSBaseClassConfig


from rq import Queue
from redis import Redis
from rq.decorators import job
from importlib.machinery import SourceFileLoader


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

        self.static_files = {}
        self._sig_handler = []
        self.cmds_meta = {}
        self.classes = {}
        self.cmds = {}  #will be dynamically loaded while the server is being used
        self.schema_urls = []
        self.serializer = None

        self.ssl_priv_key_path = None
        self.ssl_cert_path = None

        self.host = self.config.data["host"]
        self.port = int(self.config.data["port"])
        self.address = '{}:{}'.format(self.host, self.port)
        # self.app_dir = self.config.data["app_dir"]
        self.ssl = self.config.data["ssl"]

        self.web_client_code = None
        self.code_generated_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "gedis", self.instance, "server")

        # self.jsapi_server = JSAPIServer()
        self.chatbot = GedisChatBotFactory(ws=self)

        redis_conn = Redis()
        self.workers_queue =  Queue(connection=redis_conn)
        self.workers_jobs = {}
        self.cmd_paths = []

        self.logger_enable()



    #######################################CODE GENERATION

    def code_generate_model_actors(self):
        """
        generate the actors (methods to work with model) for the model and put in code generated dir
        """
        reset=True
        self.logger.info("Generate models & populate self.schema_urls")
        self.logger.info("in: %s"%self.code_generated_dir)
        for namespace, model in j.data.bcdb.latest.models.items():

            # url = table.schema.url.replace(".","_")
            self.logger.info("generate model: model_%s.py" % namespace)
            namespace_ = namespace.replace(".","_")
            dest = j.sal.fs.joinPaths(self.code_generated_dir, "model_%s.py" % namespace_)
            if reset or not j.sal.fs.exists(dest):
                # find_args = ''.join(["{0}={1},".format(p.name, p.default_as_python_code) for p in table.schema.properties if p.index]).strip(',')
                # kwargs = ''.join(["{0}={0},".format(p.name, p.name) for p in table.schema.properties if p.index]).strip(',')
                code = j.tools.jinja2.file_render("%s/templates/actor_model_server.py"%(j.servers.gedis.path),
                                                    dest=dest,
                                                    schema=model.schema,model=model)

                # self.logger.debug("cmds generated add:%s" % item)
                self.cmds_add(namespace, path=dest)

            self.schema_urls.append(model.schema.url)

    def code_generate_js_client(self):
        """
        "generate the code for the javascript browser
        """
        # generate web client
        commands = []

        for nsfull, cmds_ in self.cmds_meta.items():
            if 'model_' in nsfull:
                continue
            commands.append(cmds_)
        self.code_js_client = j.tools.jinja2.file_render("%s/templates/client.js" % j.servers.gedis.path,
                                                         commands=commands,write=False)


    def cmds_add(self, name, path):
        """
        add commands from 1 actor (or other python) file

        :param name:  each set of cmds need to have a unique name
        :param path: of the actor file
        :return:
        """
        if j.sal.fs.isDir(path):
            files = j.sal.fs.listFilesAndDirsInDir(path, recursive=False, filter="*.py")
            for path2 in files:
                basepath = j.sal.fs.getBaseName(path2)
                if not "__" in basepath and not basepath.startswith("test"):
                    name2 = "%s_%s"%(name,j.sal.fs.getBaseName(path2)[:-3])
                    self.cmds_add(name2,path2)
            return

        if not j.sal.fs.exists(path):
            raise RuntimeError("cannot find actor:%s"%path)
        self.logger.debug("cmds_add:%s:%s"%(name,path))
        self.cmds_meta[name] = GedisCmds(self, path=path, name=name)

    ##########################CLIENT FROM SERVER #######################

    def client_get(self):
    
        data ={}
        data["host"] = self.config.data["host"]
        data["port"] = self.config.data["port"]
        data["adminsecret_"] = self.config.data["adminsecret_"]
        data["ssl"] = self.config.data["ssl"]
        
        return j.clients.gedis.get(instance=self.instance, data=data, reset=False,configureonly=False)

    def client_configure(self):

        data = {}
        data["host"] = self.config.data["host"]
        data["port"] = self.config.data["port"]
        data["adminsecret_"] = self.config.data["adminsecret_"]
        data["ssl"] = self.config.data["ssl"]

        return j.clients.gedis.get(instance=self.instance, data=data, reset=False, configureonly=True)

    #######################PROCESSING OF CMDS ##############

    def job_schedule(self,method, timeout=60,wait=False,depends_on=None, **kwargs):
        """
        @return job, waiter_greenlet
        """
        job = self.workers_queue.enqueue_call(func=method,kwargs=kwargs, timeout=timeout,depends_on=depends_on)
        greenlet = gevent.spawn(waiter, job)
        job.greenlet=greenlet
        self.workers_jobs[job.id]=job
        if wait:
            greenlet.get(block=True, timeout=timeout)
        return job

    # def get_command(self, cmd):
    #
    #     from pudb import set_trace;
    #     set_trace()
    #
    #     if cmd in self.cmds:
    #         return self.cmds[cmd], ''
    #
    #
    #
    #     self.logger.debug('(%s) command cache miss')
    #
    #     if '.' not in cmd:
    #         j.shell()
    #         return None, 'Invalid command (%s) : model is missing. proper format is {model}.{cmd}'
    #
    #     pre, post = cmd.split(".", 1)
    #
    #     namespace = self.instance + "." + pre
    #
    #     if namespace not in self.classes:
    #         return None, "Cannot find namespace:%s " % (namespace)
    #
    #     if namespace not in self.cmds_meta:
    #         return None, "Cannot find namespace:%s" % (namespace)
    #
    #     meta = self.cmds_meta[namespace]
    #
    #     if not post in meta.cmds:
    #         return None, "Cannot find method with name:%s in namespace:%s" % (post, namespace)
    #
    #     cmd_obj = meta.cmds[post]
    #
    #     try:
    #         cl = self.classes[namespace]
    #         m = getattr(cl, post)
    #     except Exception as e:
    #         return None, "Could not execute code of method '%s' in namespace '%s'\n%s" % (pre, namespace, e)
    #
    #     cmd_obj.method = m
    #
    #     self.cmds[cmd] = cmd_obj
    #
    #     return self.cmds[cmd], ""

    # @staticmethod
    # def process_command(cmd, request):
    #
    #     from pudb import set_trace;
    #     set_trace()
    #
    #     if cmd.schema_in:
    #         if not request.get("args"):
    #             return None, "need to have arguments, none given"
    #
    #         o = cmd.schema_in.get(data=j.data.serializers.json.loads(request["args"]))
    #         args = [a.strip() for a in cmd.cmdobj.args.split(',')]
    #         if 'schema_out' in args:
    #             args.remove('schema_out')
    #         params = {}
    #         schema_dict = o._ddict
    #         if len(args) == 1:
    #             if args[0] in schema_dict:
    #                 params.update(schema_dict)
    #             else:
    #                 params[args[0]] = o
    #         else:
    #             params.update(schema_dict)
    #
    #         if cmd.schema_out:
    #             params["schema_out"] = cmd.schema_out
    #     else:
    #         if request.get("args"):
    #             params = request["args"]
    #             if cmd.schema_out:
    #                 params.append(cmd.schema_out)
    #         else:
    #             params = None
    #
    #     try:
    #         if params is None:
    #             result = cmd.method()
    #         elif j.data.types.list.check(params):
    #             result = cmd.method(*params)
    #         else:
    #             result = cmd.method(**params)
    #         return result, None
    #
    #     except Exception as e:
    #         print("exception in redis server")
    #         eco = j.errorhandler.parsePythonExceptionObject(e)
    #         msg = str(eco)
    #         msg += "\nCODE:%s:%s\n" % (cmd.namespace, cmd.name)
    #         print(msg)
    #         return None, e.args[0]

    #######################INITIALIZATION ##################

    def _init(self):

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

        self.cmds_add("system","%s/systemactors" % j.servers.gedis.path)  # add the system actors

        # add the cmds to the server (from generated dir + app_dir)
        # bcdb should be already known otherwise we cannot generate
        self.code_generate_model_actors()  # make sure we have the actors generated for the model, is in server on code generation dir
        self.code_generate_js_client()

        self._servers_init()

        self._inited = True

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


    def _servers_init(self):

        self._sig_handler.append(gevent.signal(signal.SIGINT, self.stop))

        # from gevent import monkey
        # monkey.patch_thread() #TODO:*1 dirty hack, need to use gevent primitives, suggest to add flask server
        # import threading

        if self.ssl:
            self.ssl_priv_key_path, self.ssl_cert_path = self.sslkeys_generate()
            # Server always supports SSL
            # client can use to talk to it in SSL or not
            self.redis_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=RedisRequestHandler(self.instance, self.cmds, self.classes, self.cmds_meta).handle,
                keyfile=self.ssl_priv_key_path,
                certfile=self.ssl_cert_path
            )
        else:
            self.redis_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=RedisRequestHandler(self.instance, self.cmds, self.classes, self.cmds_meta).handle
            )


    def start(self):
        """
        this method is only used when not used in digitalme
        """
        self._init()

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

