from Jumpscale import j
import gevent

from .Community import Community
from .ServerRack import ServerRack
from gevent import time
import gevent

JSBASE = j.application.JSBaseClass


class DigitalMe(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.servers.digitalme"
        JSBASE.__init__(self)
        self.filemonitor = None
        self.community = Community()


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
