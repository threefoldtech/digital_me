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
sshport_last = 4010
redis_address = ""
redis_port = 0
"""

import time

class ZOS(BASE):

    def __init__(self, zosclient,name):

        self._zos_private_address = None
        self._schema = j.data.schema.get(schema)
        self._redis_key="config:zos"

        BASE.__init__(self,zosclient=zosclient,name=name)



    def __repr__(self):
        return "zos:%s" % self.name

    __str__ = __repr__
