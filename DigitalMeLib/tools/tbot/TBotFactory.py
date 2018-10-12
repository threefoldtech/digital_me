from Jumpscale import j
from DigitalMeLib.tools.builder.ZOSContainer import ZOSContainer
import re
from io import StringIO
import os
import locale

JSBASE = j.application.JSBaseClass

from .TBot import TBot

class TBotFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.tools.tbot"
        JSBASE.__init__(self)
        self._tbots={}
        self.logger_enable()


    def init(self,addr="localhost",port=4444,secret=""):


    def zos_client_get(self):
        j.shell()



    def get(self,name="3bot",zosclient=None):
        if name not in self._tbots:
            node = j.tools.nodemgr.set(cat="container", name=name, sshclient=name, selected=False)
            if not zosclient:
                zosclient = self.zos_client_get()
            zos_container = ZOSContainer(zosclient=zosclient, node=node)
            self._tbots[name] = TBot(zoscontainer=zos_container)
        return self._tbots[name]


    def test(self):
        """
        js_shell 'j.tools.tbot.test()'
        """
        bot = self.get()
        print(bot.node)
        j.shell()
