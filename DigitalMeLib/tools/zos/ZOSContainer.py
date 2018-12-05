from Jumpscale import j
from watchdog.observers import Observer
from .MyFileSystemEventHandler import MyFileSystemEventHandler
JSBASE = j.application.JSBaseClass
import time
class ZOSContainer(JSBASE):

    def __init__(self,zos,data):
        self.zos = zos
        self.__dict__.update(data)
        self._node = None

        if "address" not in data:
            self.address=self.zos.address

        self.port_ssh = None

        for p in self.ports.split(","):
            outside,inside = p.split(":")
            inside=int(inside)
            outside=int(outside)
            if inside==22:
                self.port_ssh = outside

    @property
    def node(self):
        if self._node==None:
            name="zos_%s_%s"%(self.zos.name,self.name)
            data={}
            data["name"]=name
            data["sshclient"]= name
            data["active"]=True
            data["selected"]=True

            sshclient = j.clients.ssh.new(addr=self.address, port=self.port_ssh, instance=name, keyname="", timeout=5, allow_agent=True)

            node = j.tools.nodemgr.get(name,data=data)

            self._node=node
        return self._node

    def sync(self, monitor=False,paths=["$CODEDIR/github/threefoldtech/jumpscale_core",
                                        "$CODEDIR/github/threefoldtech/jumpscale_lib",
                                        "$CODEDIR/github/threefoldtech/jumpscale_prefab",
                                        "$CODEDIR/github/threefoldtech/digital_me"]):
        """
        sync all code to the remote destinations, uses config as set in jumpscale.toml

        """
        self.node.sync(paths=paths)
        self.sync_paths = paths
        if monitor:
            self._monitor(paths=paths)

    def _monitor(self,paths):
        """
        look for changes in directories which are being pushed & if found push to remote nodes

        js_shell 'j.tools.develop.monitor()'
        """

        event_handler = MyFileSystemEventHandler(zoscontainer=self)
        observer = Observer()
        for source in paths:
            self.logger.info("monitor:%s" % source)
            source2 = j.tools.prefab.local.core.replace(source)
            observer.schedule(event_handler, source2, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
