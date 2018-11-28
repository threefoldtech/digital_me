from Jumpscale import j

JSBASE = j.application.JSBaseClass

class ZOS(JSBASE):

    def __init__(self,ipaddr,port):
        self.ipaddr = ipaddr
        self.port = int(port)



    @property
    def container_list_data(self):
        if self._list == []:
            self._list = data = self._cmd("zos container list")
        return

    @property
    def container_last_data(self):
        return container_list_data[-1]

    @property
    def container_list_hr(self):
        return j.data.serializers.yaml.dumps(self.list_data)

    @property
    def _containerlist(self):
        return [item["name"] for item in self.list_data]

    def container_get(self,name=""):
        if name=="":
            cmd = "zos container info --json"
        else:
            cmd = "zos container info"
        rc,out,err = j.sal.process.execute(cmd)

    def sync(self):
        """
        sync all code to the remote destinations, uses config as set in jumpscale.toml

        """


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
