from Jumpscale import j

JSBASE = j.application.JSBaseClass

class ZOSContainer(JSBASE):

    def __init__(self,data):
        self.data=data





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
