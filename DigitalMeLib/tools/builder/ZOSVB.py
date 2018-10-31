from Jumpscale import j
import re
from io import StringIO
import os
import locale

from .BASE import BASE

schema = """
@url = zos.config
date_start = 0 (D)
description = ""
progress = (LS)
sshport_last = 4010
redis_address = ""
redis_port = 0

"""

import time

class ZOSVB(BASE):

    def __init__(self, zosclient,name):

        self._zos_private_address = None
        self._schema = j.data.schema.get(schema)
        self._redis_key="config:zos"

        BASE.__init__(self,zosclient=zosclient,name=name)

        self.zos_private_address #make sure we know the private addr


    @property
    def zos_private_address(self):
        """
        private addr of the virtualbox, if not virtualbox will return False
        will also do a ping test
        :return: False if no virtualbox
        """
        if self._zos_private_address == None:

            if self.model.redis_address != "":
                self._zos_private_address = self.model.redis_address
            else:
                # assume vboxnet0 use an 192.168.0.0/16 address
                for nic in self.zosclient.client.info.nic():
                    if len(nic['addrs']) == 0:
                        continue
                    if nic['addrs'][0]['addr'].startswith("192.168."):
                        self._zos_private_address = nic['addrs'][0]['addr'].split('/')[0]
                        if not j.sal.nettools.pingMachine(self._zos_private_address):
                            raise RuntimeError("could not reach private addr:%s of VB ZOS"%self._zos_private_address)
                        self.model.redis_address = self._zos_private_address
                        self.model_save()
                        return self._zos_private_address
                raise RuntimeError("could not find private addr of virtualbox for zos")
        return self._zos_private_address

    def _get_free_port(self):
        port = 4001
        while j.sal.nettools.checkListenPort(port)==True:
            self.logger.debug("check for free tcp port:%s"%port)
            port+=1
        return port




    @property
    def vb_client(self):
        """
        virtualbox client
        """
        return j.clients.virtualbox.client


    # def client(self, node):
    #     self.logger.debug("resolving private virtualbox address")
    #
    #     private = j.clients.virtualbox.zero_os_private_address(node)
    #     self.logger.info("virtualbox machine private address: %s" % private)
    #
    #     node = j.clients.zos.get('builder_private', data={'host': private})
    #     node.client.ping()
    #
    #     return node

    def __repr__(self):
        return "zosvb:%s" % self.name

    __str__ = __repr__
