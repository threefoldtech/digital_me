from Jumpscale import j

import gevent

from gevent import monkey
from .Community import Community
import time
from gevent import event, sleep

JSBASE = j.application.JSBaseClass


class DigitalWorld(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.servers.digitalworld"
        JSBASE.__init__(self)
        self.filemonitor = None
        self.community = Community()



    def test(self):
        """
        js_shell 'j.servers.digitalworld.test()'
        """

        j.shell()
