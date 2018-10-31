from Jumpscale import j
import re
from io import StringIO
import os
import locale

from .BASE import BASE

schema = """
@url = zos.container.config
date_start = 0 (D)
description = ""
name = ""
authorized = False (B)
pid = 0 (I)
container_id = 0 (I) 
progress = (LS)
flist = ""
nics = (LO) !zos.container.nic
sshport = 0 (I)

@url = zos.container.nic
type = "default"
 
"""

import time

class ZOSContainer(BASE):

    def __init__(self, zos,name):
        self.zos = zos
        self.zosclient = zos.zosclient
        # self._node = node
        self._container = None
        self._node_connected = False
        self._schema = j.data.schema.get(schema)
        self._redis_key="config:zos:container:%s"%name

        BASE.__init__(self,redis=zos._redis,name=name,schema=schema)

        self.model.flist = "https://hub.grid.tf/tf-official-apps/ubuntu-bionic-build.flist"



    @property
    def nics(self):
        """
        e.g.

        nics = '[
            {
            "type": "default"
            }
        ]'

        :return:
        """
        nics = []
        for nic in self.model.nics:
            d = {"type":nic.type}
            nics.append(d)
        return nics

    @property
    def zos_private_address(self):
        return self.zos.zos_private_address


    @property
    def name(self):
        return self.model.name

    def start(self):
        self.api

    def stop(self):
        self.api.stop()

    def _create(self):
        print('creating builder container...')
        self.model.progress=[] #make sure we don't remember old stuff
        self.model_save()


        if len(self.model.nics) == 0:
            nic = self.model.nics.new()
            nic.type = "default"
            self.model_save()
            j.shell()

        self.logger.info("create container: %s %s sshport:%s \nnics:\n%s"%
                         (self.name,self.model.flist,self.sshport,self.nics))


        self._container = self.zosclient.containers.create(name=self.name,
                                           hostname=self.name,
                                           flist=self.model.flist,
                                           nics=self.nics,
                                           ports={self.sshport: 22})

        info = self._container.info['container']
        while "pid" not in info:
            time.sleep(0.1)
            self.logger.debug("waiting for container to start")
        self.model.pid = info["pid"]
        self.model.container_id = info["id"]
        self.model_save()
        assert self._container.is_running()

    @property
    def info(self):
        # assert self.model.port == self.container.info
        return self.container.info

    @property
    def api(self):
        """
        :return: zero-os container object
        """
        if self._container is None:
            if not self.name in [item.name for item in self.zosclient.containers.list()]:
                self._create()
            self._container = self.zosclient.containers.get(self.name)
            assert self._container.is_running()
        return self._container

    @property
    def prefab(self):
        return self.node.prefab

    @property
    def node(self):
        """
        :return: node object as used in node manager, allows you to get to prefab, ...
        """
        if self._node_connected:
            return self._node

        self.start()


        if self.model.authorized is False:

            sshclient = j.clients.ssh.new(addr=self.zos_private_address, port=self.sshport, instance=self.name,
                                          die=True, login="root",passwd='rooter',
                                          stdout=True, allow_agent=False, use_paramiko=True)

            print("waiting for ssh to start for container:%s\n    (if the ZOS VM is new, will take a while, OS files are being downloaded)"%self.name)
            for i in range(50):
                try:
                    res = sshclient.connect()
                    rc,out,err=sshclient.execute("which bash")
                    if "bash" in out:
                        break
                except j.exceptions.RuntimeError as e:
                    if "Could not connect to" in str(e):
                        continue
                    raise e

            self.logger.info("ssh connected")
            key = j.clients.sshkey.list()[0]

            sshclient.ssh_authorize(user="root", key=key)

            self.model.authorized = True
            self.model_save()

            self.logger.info('container deployed')
            self.logger.info("to connect to it do: 'ssh root@%s -p %s' (password: rooter)" % (self.zos_private_address,self.model.port))
            self.logger.info("can also connect using js_node toolset, recommended: 'js_node ssh -i %s'"%self.name)
        if j.clients.ssh.get('builder').sshkey:
            key_path =j.clients.ssh.get('builder').sshkey.path
            keyname_paths=os.path.split(key_path)
            keyname = keyname_paths[len(keyname_paths)-1]
        else:
            keyname =''
        sshclient = j.clients.ssh.new(addr=self.zos_private_address,
                                      port=self.model.port, instance=self.name,
                                      die=True, login="root", keyname=keyname,
                                      stdout=True, allow_agent=True,
                                      use_paramiko=True)
        self._node_connected = True

        return self._node

    @property
    def zos_private_address(self):
        """
        """
        return self.zos.zos_private_address

    @property
    def sshport(self):

        #CHECK IF VBZOS if yes use port per SSH connection because is same ip addr
        #CHECK IF ZOS direct (no VB), then is zerotier addr with std ssh port...

        if self.model.sshport == 0:
            if self.zos.model.sshport_last==0:
               self.zos.model.sshport_last=6000
            else:
                self.zos.model.sshport_last+=1
            self.model.sshport = self.zos.model.sshport_last

        return self.model.sshport

    # def zero_os_private(self, node):
    #     self.logger.debug("resolving private virtualbox address")
    #
    #     private = j.clients.virtualbox.zero_os_private_address(node)
    #     self.logger.info("virtualbox machine private address: %s" % private)
    #
    #     node = j.clients.zos.get('builder_private', data={'host': private})
    #     node.client.ping()
    #
    #     return node


    def build_python_jumpscale(self,reset=False):

        if reset:
            self.done_reset()

        if not self.done_check("jscore_install"):
            self.prefab.jumpscale.jumpscalecore.install()
            # TODO: *1 do some tests, did jumpscale install well e.g. do an echo test with shell
            self.done_set("jscore_install")

        self.node.sync()  #sync all local jumpscale code to the container

        if not self.done_check("python_build"):
            self.prefab.runtimes.python.build()
            #TODO: *1 do some tests, did python really build well
            self.done_set("python_build")

        cmd = "js_shell 'j.tools.sandboxer.python.do(build=False)'"  #building did already happen
        self.prefab.core.run(cmd)

        #TODO:*1 add some checks in there to make sure the building happened ok
        #TODO:*1 there is bug, the packaging does not find the right directories

    def __repr__(self):
        return "container:%s" % self.name

    __str__ = __repr__
