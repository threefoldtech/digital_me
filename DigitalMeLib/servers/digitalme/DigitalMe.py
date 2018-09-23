from Jumpscale import j

import gevent

from gevent import monkey
from .Community import Community
from .ServerRack import ServerRack
from .Package import  Package
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
        for item in j.sal.fs.listFilesInDir(path, recursive=True, filter="dm_config.toml",
                                followSymlinks=False, listSymlinks=False):
            pdir = j.sal.fs.getDirName(item)
            self.package_add(pdir,zdbclients=zdbclients)
        # Generate js client code
        j.servers.gedis.latest.code_generate_last_step()

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

    def start(self,path="",nrworkers=0,name="test",zdbclients={},adminsecret="1234"):
        """
        examples:

        js_shell 'j.servers.digitalme.start()'
        js_shell 'j.servers.digitalme.start(nrworkers=4)'

        path can be git url or path

        @PARAM if zdbclients is {} then will use j.clients.zdb.testdb_server_start_client_get()
                is dict with key = namespace, default will be used for each one where namespace not defined
        """

        def install_zrobot():
            path = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/0-robot")
            j.sal.process.execute("cd %s;pip3 install -e ." % path)

        if "_zrobot" not in j.servers.__dict__.keys():
            # means not installed yet
            install_zrobot()

        if zdbclients == {}:
            zdbclients["default"] = j.clients.zdb.testdb_server_start_client_get()

        if path is not "":
            if not j.sal.fs.exists(path):
                path = j.clients.git.getContentPathFromURLorPath(path)
        else:
            path = j.clients.git.getContentPathFromURLorPath(
                "https://github.com/threefoldtech/digital_me/tree/development/packages")

        monkey.patch_all(subprocess=False)
        self.rack = self.server_rack_get()

        geventserver = j.servers.gedis.configure(host="localhost", port="8001", ssl=False,
                                  adminsecret=adminsecret, instance=name)
        # configure a local webserver server (the master one)
        j.servers.web.configure(instance=name, port=8000, port_ssl=0, host="0.0.0.0", secret=adminsecret)

        self.rack.add("gedis", geventserver.redis_server) #important to do like this, otherwise 2 servers started
        self.rack.add("web", j.servers.web.geventserver_get(name))


        if nrworkers>0:
            self.rack.workers_start(nrworkers)

        self.packages_add(path,zdbclients=zdbclients)

        j.servers.web.latest.loader.load() #loads the rules in the webserver (routes)

        self.rack.start()

    def server_rack_get(self):

        """
        returns a server rack
        """

        return ServerRack()


    def test(self, zdb_start=False):
        """
        js_shell 'j.servers.digitalme.test(zdb_start=False)'
        """

        if zdb_start:
            cl = j.clients.zdb.testdb_server_start_client_get(start=True)  # starts & resets a zdb in seq mode with name test

        cmd = "js_shell 'j.servers.digitalme.start(nrworkers=10)'"
        j.tools.tmux.execute(
            cmd,
            session='main',
            window='digitalme_test',
            pane='main',
            session_reset=False,
            window_reset=True
        )
        print ("wait till server started, will timeout in 25 sec max")
        assert j.sal.nettools.waitConnectionTest("localhost", 8000, timeoutTotal=20)
        assert j.sal.nettools.waitConnectionTest("localhost", 8001, timeoutTotal=5)

        #now means the server is up and running

        # gedisclient = j.clients.gedis.configure("test",namespace="system",port=8001,secret="1234",host="localhost")
        # j.shell()
        #
