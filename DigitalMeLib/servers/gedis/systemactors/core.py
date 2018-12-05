

from Jumpscale import j

JSBASE = j.application.JSBaseClass


class core(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.server = j.servers.gedis.latest

    # def auth(self,secret):
    #     return "OK"

    def namespaces(self, schema_out):
        """

        returns list of namespaces

        ```out
        result = (LS)
        ```
        """
        r = schema_out.new()
        r.namespaces = self.server.namespaces
        return r
