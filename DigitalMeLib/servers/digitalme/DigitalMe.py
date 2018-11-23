from Jumpscale import j

import gevent

from gevent import monkey
from .Community import Community
from .ServerRack import ServerRack
from .Package import  Package
import time
from gevent import event, sleep

JSBASE = j.application.JSBaseClass


class DigitalMe(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.servers.digitalme"
        JSBASE.__init__(self)
        self.filemonitor = None
        self.community = Community()
        self.packages= {}

    def packages_add(self,path,zdbclients):
        """

        :param path: path of packages, will look for dm_config.toml
        :return:
        """
        graphql_dir = ''
        for item in j.sal.fs.listFilesInDir(path, recursive=True, filter="dm_config.toml",
                                followSymlinks=False, listSymlinks=False):
            pdir = j.sal.fs.getDirName(item)
            # don't lopad now! defer as last package
            if pdir.endswith('graphql/'):
                graphql_dir = pdir
                continue
            self.package_add(pdir,zdbclients=zdbclients)

        # load graphql as latest package.
        # this ensures all schemas are loaded, so auto generation of queries for all loaded schemas
        # can be acheieved!
        if graphql_dir:
            self.package_add(graphql_dir, zdbclients=zdbclients)
        # Generate js client code
        j.servers.gedis.latest.code_generate_webclient()

    def package_add(self,path,zdbclients={}):
        """

        :param path: directory where there is a dm_config.toml inside = a package for digital me
        has blueprints, ...
        :return:
        """
        tpath = "%s/dm_config.toml"%path
        if not j.sal.fs.exists(tpath):
            raise j.exceptions.Input("could not find:%s"%tpath)
        p=Package(tpath,zdbclients=zdbclients)
        if p.name not in self.packages:
            self.packages[p.name]=p

    def start(self, addr="localhost",port=9900,namespace="digitalme", secret="1234",background=False):
        """

        examples:

        js_shell 'j.servers.digitalme.start()'
        js_shell 'j.servers.digitalme.start(addr="localhost",port=9900,namespace="digitalme", secret="1234")'

        :param addr: addr of starting zerodb namespace
        :param port: port
        :param namespace: name of the namespace
        :param secret: the secret of the namespace
        :return:


        """

        def install_zrobot():
            path = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/0-robot")
            j.sal.process.execute("cd %s;pip3 install -e ." % path)

        if "_zrobot" not in j.servers.__dict__.keys():
            # means not installed yet
            install_zrobot()

        if background:

            cmd = "js_shell 'j.servers.digitalme.start(addr=\"%s\",port=%s,namespace=\"%s\", secret=\"%s\")'"%\
                  (addr,port,namespace,secret)
            print (cmd)
            j.tools.tmux.execute(
                cmd,
                session='main',
                window='digitalme',
                pane='main',
                session_reset=False,
                window_reset=True
            )
            print ("wait till server started, will timeout in 25 sec max")
            time.sleep(1)
            assert j.sal.nettools.waitConnectionTest("localhost", 8000, timeoutTotal=25)
            assert j.sal.nettools.waitConnectionTest("localhost", 8001, timeoutTotal=5)


            gedisclient = j.clients.gedis.configure(namespace,namespace=namespace,port=8001,secret=secret,
                                                        host="localhost")

            j.shell()
            w


        else:

            monkey.patch_all(subprocess=False) #TODO: should try not to monkey patch, its not good practice at all
            self.rack = self.server_rack_get()

            geventserver = j.servers.gedis.configure(host="localhost", port="8001", ssl=False,
                                      adminsecret=secret, instance=namespace)
            # configure a local webserver server (the master one)
            j.servers.web.configure(instance=namespace, port=8000, port_ssl=0, host="0.0.0.0", secret=secret)

            self.rack.add("gedis", geventserver.redis_server) #important to do like this, otherwise 2 servers started
            self.rack.add("web", j.servers.web.geventserver_get(namespace))

            #the core packages, always need to be loaded
            path = j.clients.git.getContentPathFromURLorPath(
                    "https://github.com/threefoldtech/digital_me/tree/development/packages")
            zdbclient = j.clients.zdb.client_get(nsname=namespace, addr=addr, port=port, secret=secret, mode='seq')
            zdbclients = {"default":zdbclient}
            self.packages_add(path,zdbclients=zdbclients)

            j.servers.web.latest.loader.load() #loads the rules in the webserver (routes)

            self.rack.start()

    def server_rack_get(self):

        """
        returns a server rack

        to start the server manually do:
        js_shell 'j.servers.digitalme.start(namespace="test", secret="1234")'

        """

        return ServerRack()


    def test(self):
        """
        js_shell 'j.servers.digitalme.test()'
        """

        def connect_manual():
            namespace="test"
            #if server manually started can use this
            secret="1234"
            gedisclient = j.clients.gedis.configure(namespace,namespace=namespace,port=8001,secret=secret,
                                                        host="localhost")
        connect_manual()

        admincl = j.clients.zdb.testdb_server_start_client_admin_get()  # starts & resets a zdb in seq mode with name test
        cl = admincl.namespace_new("test",secret="1234")


        #gclient will be gedis client
        gcl = self.start(addr=cl.addr,port=cl.port,namespace=cl.nsname, secret=cl.secret,background=True)


        j.shell()
