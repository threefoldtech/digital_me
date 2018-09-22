

from Jumpscale import j

JSBASE = j.application.JSBaseClass

class core(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.server = j.servers.gedis.latest

    def auth(self,secret):
        return "OK"