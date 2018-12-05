import os
import signal
import sys

import gevent
from gevent import time
from gevent.pool import Pool
from gevent.server import StreamServer

from Jumpscale import j

from .GedisChatBot import GedisChatBotFactory
from .GedisCmds import GedisCmds
from .handlers import Handler

JSConfigBase = j.tools.configmanager.JSBaseClassConfig


TEMPLATE = """
    host = "0.0.0.0"
    port = 9900
    ssl = false
    adminsecret_ = ""
    """


def waiter(job):
    while job.result is None:
        time.sleep(0.1)
    return job.result


class GedisServer(JSConfigBase):
    def __init__(self, instance, data=None, parent=None, interactive=False, template=None):
        JSConfigBase.__init__(
            self,
            instance=instance,
            data=data or {},
            parent=parent,
            template=template or TEMPLATE,
            interactive=interactive)

        self._sig_handler = []

        self.cmds_meta = {}  # is the metadata of the actor
        self.classes = {}  # the code as set by the gediscmds class = actor cmds
        self.schema_urls = []  # used at python client side
        self.code_js_client = None  # generated code for javascript client #FIXME: probably not needed to keep it in memory like this

        self.ssl_priv_key_path = None
        self.ssl_cert_path = None

        self.host = self.config.data["host"]
        self.port = int(self.config.data["port"])
        self.address = '{}:{}'.format(self.host, self.port)
        self.ssl = self.config.data["ssl"]

        self.web_client_code = None
        self.code_generated_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "gedis", self.instance, "server")

        self.chatbot = GedisChatBotFactory()

        self.namespaces = ["system", "default"]

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

        self.actors_add(namespace="system", path=j.sal.fs.joinPaths(
            j.servers.gedis._dirpath, "systemactors"))  # add the system actors

        for sig in [signal.SIGINT, signal.SIGTERM]:
            self._sig_handler.append(gevent.signal(sig, self.stop))

        handler = Handler(self)
        if self.ssl:
            self.ssl_priv_key_path, self.ssl_cert_path = self.sslkeys_generate()
            # Server always supports SSL
            # client can use to talk to it in SSL or not
            self.redis_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=handler.handle_redis,
                keyfile=self.ssl_priv_key_path,
                certfile=self.ssl_cert_path
            )
        else:
            self.redis_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=handler.handle_redis
            )

    # CODE GENERATION
    def code_generate_webclient(self):
        # generate web client
        commands = list(self.cmds_meta.values())
        self.code_js_client = j.tools.jinja2.template_render("%s/templates/client.js" % j.servers.gedis._dirpath,
                                                             commands=commands)

    ########################POPULATION OF SERVER#########################

    def models_add(self, models, namespace="default"):
        """
        :param models:  e.g. bcdb.models.values() or bcdb itself
        :param namespace:
        :return:
        """
        if namespace not in self.namespaces:
            self.namespaces.append(namespace)

        reset = True  # FIXME: this mean we always reset, why ?

        # FIXME: what is models is not a list or have no models attribute ?
        if not j.data.types.list.check(models):
            if hasattr(models, "models"):
                models = models.models.values()

        for model in models:
            model_name = "model_%s.py" % (model.schema.key)
            dest = j.sal.fs.joinPaths(self.code_generated_dir, model_name)
            self.logger.info("generate model: %s at %s", model_name, dest)
            if reset or not j.sal.fs.exists(dest):
                j.tools.jinja2.template_render(
                    path=j.sal.fs.joinPaths(j.servers.gedis._dirpath, "templates/actor_model_server.py"),
                    dest=dest,
                    bcdb=model.bcdb,
                    schema=model.schema,
                    model=model)
                self.actor_add(path=dest, namespace=namespace)
            self.schema_urls.append(model.schema.url)

    def actors_add(self, path, namespace="default"):
        """
        add commands from 1 actor (or other python) file

        :param name:  each set of cmds need to have a unique name
        :param path: of the actor file
        :return:
        """
        if not j.sal.fs.isDir(path):
            raise ValueError("actor_add: path needs to point to an existing directory")

        files = j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py")
        for file_path in files:
            basepath = j.sal.fs.getBaseName(file_path)
            if "__" in basepath or basepath.startswith("test"):
                continue
            self.actor_add(file_path, namespace=namespace)

    def actor_add(self, path, namespace="default"):
        """
        add commands from 1 actor (or other python) file

        :param name:  each set of cmds need to have a unique name
        :param path: of the actor file
        :return:
        """
        if namespace not in self.namespaces:
            self.namespaces.append(namespace)

        if not j.sal.fs.exists(path):
            raise ValueError("actor_add: cannot find actor at %s" % path)

        self.logger.debug("actor_add:%s:%s", namespace, path)
        name = actor_name(path, namespace)
        key = actor_key(name, namespace)
        self.cmds_meta[key] = GedisCmds(server=self, path=path, name=name, namespace=namespace)

    ####################################################################

    def actors_list(self, namespace="default"):
        """
        list all actors loaded in the server
        optinally filter base on namespace

        :param namespace: if specified filer the actors based on the namespace used, defaults to "default"
        :param namespace: str, optional
        :return: list of actors
        :rtype: list
        """
        # TODO: unittest
        res = []
        for key, cmds in self.cmds_meta.items():
            if not namespace or key.startswith("%s__" % namespace):
                res.append(cmds)
        return res

    def actors_methods_list(self, namespace="default"):
        """
        list the actors and their methods

        return a dict like:
        {
            'actor_name': {
                'schema': "str_schema",
                'cmds': {
                    "cmd_name1": "cmd1_args",
                    "cmd_name2": "cmd2_args",
                }
            }
        }

        :param namespace: if specified filer the actors based on the namespace used, defaults to "default"
        :param namespace: str, optional
        :return: dict of actor and they commands
        :rtype: dict
        """
        # TODO: unittest
        actors = self.actors_list(namespace)
        res = {}
        for actor in actors:
            res[actor.name] = {
                'schema': str(actor.schema),
                'cmds': {cmd.name: str(cmd.args) for cmd in actor.cmds.values()},
            }
        return res

    ##########################CLIENT FROM SERVER #######################

    def client_get(self, namespace="default"):
        """
        Helper method to get a client that connect to this instance of the server

        it configure a client using the same info as the server.

        :param namespace: namespace to use, defaults to "default"
        :param namespace: str, optional
        :return: gedis client
        :rtype: GedisClient
        """

        data = {}
        data["host"] = self.config.data["host"]
        data["port"] = self.config.data["port"]
        data["adminsecret_"] = self.config.data["adminsecret_"]
        data["ssl"] = self.config.data["ssl"]
        data["namespace"] = namespace

        return j.clients.gedis.get(instance=self.instance, data=data, reset=False, configureonly=False)

    def client_configure(self, namespace="default"):
        """
        Helper method to create a gedis client instance that connect to this instance of the server

        it configure a client using the same info as the server.

        :param namespace: namespace to use, defaults to "default"
        :param namespace: str, optional
        :return: gedis client
        :rtype: GedisClient
        """

        data = {
            "host": self.config.data["host"],
            "port": self.config.data["port"],
            "adminsecret_": self.config.data["adminsecret_"],
            "ssl": self.config.data["ssl"],
            "namespace": namespace,
        }
        return j.clients.gedis.get(instance=self.instance, data=data, reset=False, configureonly=True)

    #######################PROCESSING OF CMDS ##############

    def job_schedule(self, method, timeout=60, wait=False, depends_on=None, **kwargs):
        """
        @return job, waiter_greenlet
        """
        job = self.workers_queue.enqueue_call(func=method, kwargs=kwargs, timeout=timeout, depends_on=depends_on)
        greenlet = gevent.spawn(waiter, job)
        job.greenlet = greenlet
        self.workers_jobs[job.id] = job
        if wait:
            greenlet.get(block=True, timeout=timeout)
        return job

    def sslkeys_generate(self):
        if not self.ssl:
            raise RuntimeError("sslkeys_generate: gedis server is not configure to use ssl")

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
        # WHEN USED OVER WEB, USE THE DIGITALME FRAMEWORK
        # t = threading.Thread(target=self.websocket_server.serve_forever)
        # t.setDaemon(True)
        # t.start()
        # self.logger.info("start Server on {0} - PORT: {1} - WEBSOCKETS PORT: {2}".format(self.host, self.port, self.websockets_port))
        self.logger.info("%s RUNNING", str(self))
        self.redis_server.serve_forever()

    def stop(self):
        """
        stop receiving requests and close the server
        """
        # TODO: gracefull shutdown. wait for the greenlet to finish
        # since we start the server by passing it a gevent.Pool we can control
        # all the greenlet used by the server

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


def actor_name(path, namespace):
    """
    extract the name of an actor based on its path and namespace used

    :param path: path of the actor file
    :type path: str
    :param namespace: 0-db namespace used by this actor
    :type namespace: str
    :return: key used to keep the actor in memory
    :rtype: str
    """
    # TODO: unit tests this
    name, _ = os.path.splitext(os.path.basename(path))
    if namespace in name and name.startswith("model"):
        name = "model_%s" % name.split(namespace, 1)[1].strip("_")
    return name


def actor_key(name, namespace):
    """
    generate the key used to key the actor in memory bases
    on the actor path and namespace used


    :param name: name of the actor
    :type name: str
    :param namespace: 0-db namespace used by this actor
    :type namespace: str
    :return: key used to keep the actor in memory
    :rtype: str
    """
    # TODO: unit tests this
    return "%s__%s" % (namespace, name)
