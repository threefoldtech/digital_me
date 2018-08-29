from jumpscale import j
from gevent import monkey
from .Community import Community
from .ServerRack import ServerRack
from .Package import  Package
from gevent import time
import gevent

JSBASE = j.application.jsbase_get_class()


class DigitalMe(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.servers.digitalme"
        JSBASE.__init__(self)
        self.filemonitor = None
        self.community = Community()
        self.packages= {}

    def packages_add(self,path):
        """

        :param path: path of packages, will look for dm_config.toml
        :return:
        """
        for item in j.sal.fs.listFilesInDir(path, recursive=True, filter="dm_config.toml",
                                followSymlinks=False, listSymlinks=False):
            pdir = j.sal.fs.getDirName(item)
            self.package_add(pdir)

    def package_add(self,path):
        """

        :param path: directory where there is a dm_config.toml inside = a package for digital me
        has blueprints, ...
        :return:
        """
        tpath = "%s/dm_config.toml"%path
        if not j.sal.fs.exists(tpath):
            raise j.exceptions.Input("could not find:%s"%tpath)
        p=Package(tpath)
        if p.name not in self.packages:
            self.packages[p.name]=p

    def start(self,path="",nrworkers=0):
        """
        examples:

        js_shell 'j.servers.digitalme.start()'
        js_shell 'j.servers.digitalme.start(nrworkers=4)'
        """

        self.rack = self.server_rack_get()

        def install_zrobot():
            path = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/0-robot")
            j.sal.process.execute("cd %s;pip install -e ." % path)

        if "_zrobot" not in j.servers.__dict__.keys():
            # means not installed yet
            install_zrobot()


        zdbcl=j.clients.zdb.testdb_server_start_client_get()

        pdir = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/digital_me/tree/development/packages")

        name="test"

        j.servers.gedis.configure(host="localhost", port="8001", ssl=False,
                                  zdb_instance=name, secret="", app_dir="", instance=name)
        # configure a local webserver server (the master one)
        j.servers.web.configure(instance=name, port=8000, port_ssl=0, host="localhost", secret="", ws_dir="")

        monkey.patch_all()

        self.rack.add("gedis", j.servers.gedis.geventservers_get(name))
        self.rack.add("web", j.servers.web.geventserver_get(name))

        if nrworkers>0:
            rack.workers_start(nrworkers)


        self.packages_add(pdir)


        j.shell()



        from IPython import embed; embed()
        s


    def server_rack_get(self):

        """
        returns a server rack
        """

        return ServerRack()


    def test_servers(self, zdb_start=False):
        """
        js_shell 'j.servers.digitalme.test_servers(zdb_start=False)'
        """
        rack = j.servers.digitalme.server_rack_get()

        if zdb_start:
            cl = j.clients.zdb.testdb_server_start_client_get(start=True)  # starts & resets a zdb in seq mode with name test

        ws_dir = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/digital_me/tree/development/digitalme")
        j.servers.gedis.configure(host="localhost", port="8000", ssl=False, zdb_instance="test",
                                  secret="", app_dir=ws_dir, instance='test')

        gedis_server = j.servers.gedis.geventservers_get("test")
        rack.add("gedis", gedis_server)

        # configure a local web server server (the master one)
        j.servers.web.configure(instance="test", port=5050, port_ssl=0,
                                host="0.0.0.0", secret="", ws_dir=ws_dir)

        # use jumpscale way of doing wsgi server (make sure it exists already)
        ws = j.servers.web.geventserver_get("test")
        rack.add("web", ws)
        # dnsserver=j.servers.dns.get(5355)
        # rack.add(dnsserver)

        # #simple stream server on port 1234
        # from gevent import socket
        # from gevent.server import StreamServer
        # def echo(socket, address):
        #     print('New connection')
        #     socket.sendall(b'Welcome to the echo server! Type quit to exit.\r\n')
        #     # using a makefile because we want to use readline()
        #     rfileobj = socket.makefile(mode='rb')
        #     while True:
        #         line = rfileobj.readline()
        #         if not line:
        #             print("client disconnected")
        #             break
        #         if line.strip().lower() == b'quit':
        #             print("client quit")
        #             break
        #         socket.sendall(line)
        #         print("echoed %r" % line)
        #     rfileobj.close()

        # sserver = StreamServer(('', 1234), echo,spawn=10)

        # rack.add(sserver)

        rack.start()

        gevent.sleep(1000000000)

        rack.stop()
