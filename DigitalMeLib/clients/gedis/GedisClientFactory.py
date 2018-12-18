from Jumpscale import j

JSConfigBase = j.application.JSFactoryBaseClass
from .GedisClient import GedisClient


class GedisClientCmds():
    def __init__(self):
        pass

    # @property
    # def _config(self):
    #     return self._client.config
    #
    # @property
    # def _config_template(self):
    #     return self._client.config_template

    def __str__(self):
        if self._client.config.data["ssl"]:
            return "Gedis Client: (instance=%s) (address=%s:%-4s)\n(ssl=True, certificate:%s)" % (
                self._client.instance,
                self._client.config.data["host"],
                self._client.config.data["port"],
                self._client.config.data["sslkey"]
            )

        return "Gedis Client: (instance=%s) (address=%s:%-4s)" % (
            self._client.instance,
            self._client.config.data["host"],
            self._client.config.data["port"]
        )

    __repr__ = __str__


class GedisClientFactory(JSConfigBase):
    def __init__(self):
        self.__jslocation__ = "j.clients.gedis"
        JSConfigBase.__init__(self, GedisClient)
        self._template_engine = None
        self._template_code_client = None
        self._code_model_template = None

    def get(self,instance='main',data={},reset=False,configureonly=False):

        client = JSConfigBase.get(self,instance=instance, data=data, reset=reset,
                                                     configureonly=configureonly)
        if configureonly:
            print("CONFIGURE ONLY")
            return

        if client._connected:
            cl = GedisClientCmds()
            cl._client = client
            cl.models = client.models
            cl.__dict__.update(cl._client.cmds.__dict__)
            return cl



    def configure(
        self,
        instance="main",
        host="localhost",
        port=5000,
        secret="",
        namespace="default",
        ssl=False,
        ssl_cert_file="",
        reset=False, get=True
        ):

        data = {}

        data["host"] = host
        data["port"] = str(port)
        data["namespace"] = namespace
        data["adminsecret_"] = secret
        data["ssl"] = ssl
        data['sslkey'] = ssl_cert_file

        if get:
            return self.get(instance=instance, data=data, reset=reset)

