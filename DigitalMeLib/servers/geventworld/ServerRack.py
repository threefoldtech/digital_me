
from jumpscale import j
import os
import sys
from importlib import import_module
JSBASE = j.application.jsbase_get_class()
from gevent import spawn
import gevent

class ServerRack(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.servers = {}

    def add(self,name,server):
        self.servers[name]=server

    def start(self):
        #TODO:*1
        started = []
        try:
            for key,server in self.servers.items():
                server.start()
                started.append(server)
                name = getattr(server, 'name', None) or server.__class__.__name__ or 'Server'
                self.logger.info('%s started on %s', name, server.address)
        except:
            self.stop(started)
            raise

    def stop(self, servers=None):
        self.logger.info("stopping server rack")
        if servers is None:
            servers = [item[1] for item in  self.servers.items()]
        for server in servers:
            try:
                server.stop()
            except:
                if hasattr(server, 'loop'): # gevent >= 1.0
                    server.loop.handle_error(server.stop, *sys.exc_info())
                else: # gevent <= 0.13
                    import traceback
                    traceback.print_exc()


