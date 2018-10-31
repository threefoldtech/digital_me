from Jumpscale import j
import re
from io import StringIO
import os
import locale

from .BASE import BASE

schema = """
@url = zos.config
date_start = 0 (D)
description = ""
progress = (LS)
address_private = ""
sshport_last = 4010

"""

import time

class ZOS(BASE):

    def __init__(self, zosclient,name):
        self.zosclient = zosclient
        if zosclient.client._Client__redis is None:
            zosclient.ping()  # otherwise the redis client does not work
        self._redis_key="config:zos:%s"%name
        BASE.__init__(self,redis=self.zosclient.client._Client__redis,name=name,schema=schema)


    def container_get(self,name="builder",flist=""):
        from .ZOSContainer import ZOSContainer
        zc = ZOSContainer(zos=self, name=name)
        if flist is not "":
            zc.model.flist = flist
        zc.start()
        return zc

    def __repr__(self):
        return "zos:%s" % self.name

    __str__ = __repr__
