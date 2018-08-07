from jumpscale import j
from .MulticastClient import MulticastClient

JSConfigBase = j.tools.configmanager.base_class_configs


class MulticastFactory(JSConfigBase):
    def __init__(self):
        self.__jslocation__ = "j.clients.multicast"
        JSConfigBase.__init__(self, MulticastClient)
