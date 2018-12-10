
import os
import sys
from importlib import import_module

import gevent
from gevent import event, spawn

from Jumpscale import j

JSBASE = j.application.JSBaseClass


class ServerRack(JSBASE):
    """
    is a group of gedis servers in a virtual rack
    """

    def __init__(self):
        JSBASE.__init__(self)
        self.servers = {}

    def add(self, name, server):
        """
        add a gevent server e.g

        - gedis_server = j.servers.gedis.geventservers_get("test")
        - web_server = j.servers.web.geventserver_get("test")

        can then add them

        REMARK: make sure that subprocesses are run before adding gevent servers

        """
        self.servers[name] = server

    def filemonitor_start(self, gedis_instance_name=None, subprocess=True):
        """
        @param gedis_instance_name: gedis instance name that will be monitored

        js_shell 'j.servers.digitalme.filemonitor_start("test",subprocess=False)'
        """
        from .FileSystemMonitor import monitor_changes_subprocess, monitor_changes_parent
        if subprocess:
            self.filemonitor = monitor_changes_parent(gedis_instance_name=gedis_instance_name)
        else:
            monitor_changes_subprocess(gedis_instance_name=gedis_instance_name)

    def zrobot_start(self):
        # FIXME:
        # get zrobot instance
        self.zrobot = j.servers.zrobot.get(name,
                                           data={"template_repo": "git@github.com:threefoldtech/0-templates.git",
                                                 "block": False})

    def start(self):
        started = []
        try:
            for key, server in self.servers.items():
                server.start()
                started.append(server)
                name = getattr(server, 'name', None) or server.__class__.__name__ or 'Server'
                self.logger.info('%s started on %s' % (name, server.address))
        except:
            self.stop(started)
            raise

        forever = event.Event()
        try:
            forever.wait()
        except KeyboardInterrupt:
            self.stop()

    def stop(self, servers=None):
        self.logger.info("stopping server rack")
        if servers is None:
            servers = [item[1] for item in self.servers.items()]
        for server in servers:
            try:
                server.stop()
            except:
                if hasattr(server, 'loop'):  # gevent >= 1.0
                    server.loop.handle_error(server.stop, *sys.exc_info())
                else:  # gevent <= 0.13
                    import traceback
                    traceback.print_exc()
