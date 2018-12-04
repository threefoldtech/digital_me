from Jumpscale import j

import gevent

from gevent import monkey
# from .Community import Community
from .ServerRack import ServerRack
from .Package import Package
import time
from gevent import event, sleep
import os
JSBASE = j.application.JSBaseClass


class DigitalMe(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.servers.digitalme"
        JSBASE.__init__(self)
        self.filemonitor = None
        # self.community = Community()
        self.packages= {}

    # def packages_add(self,path,zdbclients):
    #     """
    #
    #     :param path: path of packages, will look for dm_package.toml
    #     :return:
    #     """
    #     graphql_dir = ''
    #     for item in j.sal.fs.listFilesInDir(path, recursive=True, filter="dm_package.toml",
    #                             followSymlinks=False, listSymlinks=False):
    #         pdir = j.sal.fs.getDirName(item)
    #         # don't lopad now! defer as last package
    #         if pdir.endswith('graphql/'):
    #             graphql_dir = pdir
    #             continue
    #         self.package_add(pdir,zdbclients=zdbclients)
    #
    #     # load graphql as latest package.
    #     # this ensures all schemas are loaded, so auto generation of queries for all loaded schemas
    #     # can be acheieved!
    #     if graphql_dir:
    #         self.package_add(graphql_dir, zdbclients=zdbclients)
    #     # Generate js client code
    #     j.servers.gedis.latest.code_generate_webclient()

    def package_add(self,path,bcdb):
        """

        :param path: directory where there is a dm_package.toml inside = a package for digital me
        has blueprints, ...
        :return:
        """
        if not j.sal.fs.exists(path):
            raise j.exceptions.Input("could not find:%s"%path)
        p=Package(path_config=path,bcdb=bcdb)
        if p.name not in self.packages:
            self.packages[p.name]=p

    def start(self, addr="localhost",port=9900,namespace="digitalme", secret="1234",background=False):
        """

        examples:

        js_shell 'j.servers.digitalme.start()'
        js_shell 'j.servers.digitalme.start(background=True)'

        :param addr: addr of starting zerodb namespace
        :param port: port
        :param namespace: name of the namespace
        :param secret: the secret of the namespace
        :return:


        """

        #make sure we have redis running
        j.clients.redis.core_get()

        # def install_zrobot():
        #     path = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/0-robot")
        #     j.sal.process.execute("cd %s;pip3 install -e ." % path)
        #
        # if "_zrobot" not in j.servers.__dict__.keys():
        #     # means not installed yet
        #     install_zrobot()





        if background:

            env={}
            env["addr"]=addr
            env["port"]=port
            env["namespace"]=namespace
            env["secret"]=secret
            cmd_="js_shell 'j.servers.digitalme.start()"
            cmd = j.tools.tmux.cmd_get(name="digitalme",pane="p13",cmd=cmd_, env=env,process_strings=["digitalme.start"])
            cmd.stop()
            cmd.start()

            gedisclient = j.clients.gedis.configure(namespace,namespace="system",port=8001,secret=secret,
                                                        host="localhost")

            assert gedisclient.system.ping() == b"PONG"

            return gedisclient


        else:

            if "addr" in os.environ:
                addr = os.environ["addr"]
            if "port" in os.environ:
                port = int(os.environ["port"])
            if "namespace" in os.environ:
                namespace = os.environ["namespace"]
            if "secret" in os.environ:
                secret = os.environ["secret"]


            self.rack = self.server_rack_get()

            geventserver = j.servers.gedis.configure(host="localhost", port="8001", ssl=False,
                                      adminsecret=secret, instance=namespace)

            self.rack.add("gedis", geventserver.redis_server) #important to do like this, otherwise 2 servers started

            zdbclient = j.clients.zdb.client_get(nsname=namespace, addr=addr, port=port, secret=secret, mode='seq')
            key = "%s_%s_%s"%(addr,port,namespace)

            self.bcdb = j.data.bcdb.new("digitalme_%s"%key, zdbclient=zdbclient, cache=True)

            self.web_reload()

            self.rack.start()

        #get sockexec to run
        cmd = j.tools.tmux.cmd_get(name="runner",pane="p14",cmd="rm -f /tmp/exec.sock;sockexec /tmp/exec.sock")
        cmd.stop()
        cmd.start()

        j.servers.openresty.start()


    def web_reload(self):

        #add configuration to openresty
        staticpath = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/jumpscale_weblibs/tree/master/static")

        j.servers.openresty.configs_add(j.sal.fs.joinPaths(self._dirpath,"web_config"),args={"staticpath":staticpath})


        bcdb = self.bcdb

        #the core packages, always need to be loaded
        toml_path = j.clients.git.getContentPathFromURLorPath(
                "https://github.com/threefoldtech/digital_me/tree/development960/packages/system/base")
        self.package_add(toml_path,bcdb=bcdb)
        toml_path = j.clients.git.getContentPathFromURLorPath(
                "https://github.com/threefoldtech/digital_me/tree/development960/packages/system/chat")
        self.package_add(toml_path,bcdb=bcdb)
        toml_path = j.clients.git.getContentPathFromURLorPath(
                "https://github.com/threefoldtech/digital_me/tree/development960/packages/system/example")
        self.package_add(toml_path,bcdb=bcdb)


        # j.servers.openresty.start()
        # j.servers.openresty.reload()


    def server_rack_get(self):

        """
        returns a server rack

        to start the server manually do:
        js_shell 'j.servers.digitalme.start(namespace="test", secret="1234")'

        """

        return ServerRack()


    def test(self,manual=False):
        """
        js_shell 'j.servers.digitalme.test()'
        js_shell 'j.servers.digitalme.test(manual=True)'

        :param manual means the server is run manually using e.g. js_shell 'j.servers.digitalme.start()'

        """

        admincl = j.clients.zdb.testdb_server_start_client_admin_get()  # starts & resets a zdb in seq mode with name test
        cl = admincl.namespace_new("test",secret="1234")

        if manual:
            namespace="system"
            #if server manually started can use this
            secret="1234"
            gedisclient = j.clients.gedis.configure(namespace,namespace=namespace,port=8001,secret=secret,
                                                        host="localhost")
        else:
            #gclient will be gedis client
            gedisclient = self.start(addr=cl.addr,port=cl.port,namespace=cl.nsname, secret=cl.secret,background=True)

        # ns=gedisclient.core.namespaces()
        j.shell()

