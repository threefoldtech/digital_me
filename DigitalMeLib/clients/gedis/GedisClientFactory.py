from Jumpscale import j

from .GedisClient import GedisClient

JSConfigBase = j.tools.configmanager.JSBaseClassConfigs


class GedisClientCmds:

    def __init__(self, client):
        self._client = client
        self.models = client.models
        self.__dict__.update(client.cmds.__dict__)

    def __str__(self):
        output = "Gedis Client: (instance=%s) (address=%s:%-4s)" % (
            self._client.instance,
            self._client.config.data["host"],
            self._client.config.data["port"]
        )
        if self._client.config.data["ssl"]:
            # FIXME: we should probably NOT print the key. this is VERY private information
            output += "\n(ssl=True, certificate:%s)" % self._client.config.data["sslkey"]
        return output

    __repr__ = __str__


class GedisClientFactory(JSConfigBase):
    def __init__(self):
        self.__jslocation__ = "j.clients.gedis"
        JSConfigBase.__init__(self, GedisClient)
        self._template_engine = None
        self._template_code_client = None
        self._code_model_template = None

    def get(self, instance='main', data=None, reset=False, configureonly=False):

        client = JSConfigBase.get(self, instance=instance, data=data or {}, reset=reset,
                                  configureonly=configureonly)
        if configureonly:
            return

        if client._connected:
            return GedisClientCmds(client)

    def configure(self, instance="main", host="localhost", port=5000, secret="", namespace="default",
                  ssl=False, ssl_cert_file="", reset=False,):
        data = {
            "host": host,
            "port": str(port),
            "namespace": namespace,
            "adminsecret_": secret,
            "ssl": ssl,
            'sslkey': ssl_cert_file,
        }
        return self.get(instance=instance, data=data, reset=reset)
