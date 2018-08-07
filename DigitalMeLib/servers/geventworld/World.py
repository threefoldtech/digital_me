from jumpscale import j
import gevent
from .ActorCommunity import ActorCommunity
from .Actor import Actor
from .ServerRack import ServerRack
from .ChangeWatchdog import ChangeWatchdog
import time
import gipc
JSBASE = j.application.jsbase_get_class()


class Worlds(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.servers.gworld"
        JSBASE.__init__(self)

    def community_get(self):
        return ActorCommunity()

    def server_rack_get(self, gedis_instance=None):
        """
        returns a server rack
        :param monitor: if True a gedis instance name should be provided for monitoring
        :param gedis_instance_name: gedis instance name that will be monitored
        :return: server rack
        """
        if gedis_instance:
            gipc.start_process(self.monitor_changes, (gedis_instance,))
        return ServerRack()

    def actor_class_get(self):
        return Actor

    def monitor_changes(self, gedis_instance_name):
        """
        js_shell 'j.servers.gworld.monitor_changes("test")'
        """
        from watchdog.observers import Observer
        connected = False
        while not connected:
            try:
                time.sleep(2)
                cl = j.clients.gedis.get(gedis_instance_name)
                connected = True
            except Exception:
                connected = False

        event_handler = ChangeWatchdog(client=cl)
        observer = Observer()

        res =  cl.system.filemonitor_paths()
        for source in res.paths:
            self.logger.debug("monitor:%s" % source)
            observer.schedule(event_handler, source, recursive=True)

        self.logger.info("are now observing filesystem changes")
        observer.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass         

    def test_actors(self):
        """
        js_shell 'j.servers.gworld.test_actors()'
        """
        community = j.servers.gworld.community_get()
        community.actor_dna_add()
        r1 = community.actor_get("kristof.mailprocessor", "main")
        r2 = community.actor_get("kristof.mailprocessor", "failback")

        for i in range(100):
            assert (0, 11) == r2.action_ask("task1", 10)  # returns resultcode & result

        assert True == r2.monitor_running()
        assert True == r2.running()

        community.start()

    def test_servers(self, zdb_start=False):
        """
        js_shell 'j.servers.gworld.test_servers(zdb_start=False)'
        """
        rack = j.servers.gworld.server_rack_get()

        if zdb_start:
            cl = j.clients.zdb.testdb_server_start_client_get(
                start=True)  # starts & resets a zdb in seq mode with name test

        ws_dir = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/digital_me/tree/development/digitalme")
        j.servers.gedis.configure(host="localhost", port="8000", ssl=False, zdb_instance="test",
                                  secret="", app_dir=ws_dir, instance='test')

        redis_server = j.servers.gedis.geventservers_get("test")
        rack.add("gedis", redis_server)

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
