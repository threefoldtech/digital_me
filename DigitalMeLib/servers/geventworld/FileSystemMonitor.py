
from jumpscale import j

JSBASE = j.application.jsbase_get_class()
from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer
import gipc
from gevent import time

def monitor_changes_parent(gedis_instance_name):
    cend, pend = gipc.pipe(duplex=True)  #cend = client end, pend=parent end
    gipc.start_process(monitor_changes_subprocess, (gedis_instance_name,cend,))   
    try:
        while True:
            time.sleep(1)
            print(pend.get())
    except KeyboardInterrupt:
        pass   


def monitor_changes_subprocess(gedis_instance_name,cend):
    """
    js_shell 'j.servers.gworld.monitor_changes("test")'
    """
    cend.put("log: init monitor fs")
    from watchdog.observers import Observer
    connected = False
    while not connected:
        try:
            time.sleep(2)
            cl = j.clients.gedis.get(gedis_instance_name)
            connected = True
        except Exception:
            connected = False

    cend.put("log: gedis connected")

    event_handler = ChangeWatchdog(client=cl)
    observer = Observer()

    res =  cl.system.filemonitor_paths()
    for source in res.paths:
        cend.put("log: monitor:%s" % source)
        observer.schedule(event_handler, source, recursive=True)

    cend.put("log: are now observing filesystem changes")
    observer.start()
    try:
        while True:
            time.sleep(20)
            cend.put("filesystem monitor alive")
    except KeyboardInterrupt:
        pass   


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
