from Jumpscale import j

JSBASE = j.application.JSBaseClass

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

    def sync(self):
        """
        sync all code to the remote destinations, uses config as set in jumpscale.toml

        """
        j.shell()



    def monitor(self):
        """
        look for changes in directories which are being pushed & if found push to remote nodes

        js_shell 'j.tools.develop.monitor()'

        """

        # self.sync()
        # nodes = self.nodes.getall()
        # paths = j.tools.develop.codedirs.getActiveCodeDirs()

        event_handler = MyFileSystemEventHandler()
        observer = Observer()
        for source in self.getActiveCodeDirs():
            self.logger.info("monitor:%s" % source)
            observer.schedule(event_handler, source.path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
