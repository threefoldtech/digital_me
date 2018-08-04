
from jumpscale import j

JSBASE = j.application.jsbase_get_class()
from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer



class ChangeWatchdog(FileSystemEventHandler, JSBASE):
    def __init__(self,client):
        JSBASE.__init__(self)
        self.client=client
        self.logger_enable()

    def handler(self, event, action=""):
        self.logger.debug("%s:%s" % (event, action))

        changedfile = event.src_path

        if changedfile.find("/.git/") != -1:
            return
        elif changedfile.find("/__pycache__/") != -1:
            return
        elif changedfile.endswith(".pyc"):
            return

        self.client.system.filemonitor_event(is_directory=event.is_directory,\
                src_path=event.src_path,  event_type=event.event_type)


    def on_moved(self, event):
        self.handler(event, action="")

    def on_created(self, event):
        self.handler(event)

    def on_deleted(self, event):
        self.handler(event, action="")

    def on_modified(self, event):
        self.handler(event)
