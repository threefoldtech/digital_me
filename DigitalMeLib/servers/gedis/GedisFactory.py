from Jumpscale import j

from .GedisCmds import GedisCmds
from .GedisServer import GedisServer

JSConfigBase = j.tools.configmanager.JSBaseClassConfigs


class GedisFactory(JSConfigBase):
    def __init__(self):
        self.__jslocation__ = "j.servers.gedis"

        JSConfigBase.__init__(self, GedisServer)

        self._template_engine = None
        self._template_code_server = None
        self._code_model_template = None
        self._code_start_template = None
        self._code_test_template = None
        self._js_client_template = None

    def get(self, instance='main', data=None, interactive=False):
        """
        Get a gedis server instance


        :param instance: intance name, defaults to 'main'
        :param instance: str, optional
        :param data: configuration data, example:
                    host = "0.0.0.0"
                    port = 9900
                    ssl = false
                    adminsecret_ = ""
        :param data: dict, optional
        :param interactive: if True and the instance doesn't exist
                            open a ncurs form to fill the configuration,
                            defaults to False
        :param interactive: bool, optional
        :return: Gedis server object
        :rtype: GedisServer
        """
        return super(GedisFactory, self).get(instance=instance, data=data or {}, interactive=interactive)

    def geventserver_get(self, instance="main"):
        """
        return redis_server

        j.servers.gedis.geventserver_get("test")
        """
        # FIXME: this should not be needed. it is used to allow to
        # add the gevent server used by gedis to the digital me "rack"
        # instead the digitalme rack should take the GedisServer directly
        server = self.get(instance=instance)
        return server.redis_server

    def configure(self, instance="test", port=8889, host="localhost",
                  ssl=False, adminsecret="", configureclient=True):
        """
        Helper method to configure a server instance
        """
        data = {
            "port": str(port),
            "host": host,
            "adminsecret_": adminsecret,
            "ssl": ssl,
        }

        server = self.get(instance, data, interactive=False)
        if configureclient:
            server.client_configure()
        return server

    def _cmds_get(self, key, capnpbin):
        """
        Used in client only, starts from capnpbin (python client)
        """
        namespace, name = key.split("__")
        return GedisCmds(namespace=namespace, name=name, capnpbin=capnpbin)

    # def test_server_start(self):
    #     """
    #     this method is only used when not used in digitalme
    #     js_shell 'j.servers.gedis.test_server_start()'

    #     """
    #     gedis = self.get(instance="test")

    #     # zdb_cl = j.clients.zdb.testdb_server_start_client_get(reset=False)
    #     zdb_cl = j.clients.zdb.testdb_server_start_client_admin_get(reset=False)
    #     bcdb = j.data.bcdb.new('test', zdb_cl)
    #     path = j.clients.git.getContentPathFromURLorPath(
    #         "https://github.com/threefoldtech/digital_me/tree/development_960/packages/examples/models")
    #     bcdb.models_add(path=path)

    #     path = j.clients.git.getContentPathFromURLorPath(
    #         "https://github.com/threefoldtech/digital_me/tree/development_960/packages/examples/actors")
    #     gedis.actors_add(namespace="gedis_examples", path=path)
    #     gedis.models_add(namespace="gedis_examples", models=bcdb)

    #     gedis.start()

    # def test(self, zdb_start=True):
    #     """
    #     js_shell 'j.servers.gedis.test(zdb_start=False)'
    #     """
    #     if zdb_start:
    #         # remove configuration of the gedis factory
    #         self.delete("test")
    #         cl = j.clients.zdb.testdb_server_start_client_admin_get(reset=True)

    #     gedis = self.configure(instance="test", port=8888, host="localhost", ssl=False,
    #                            adminsecret="123456", interactive=False)

    #     print("START GEDIS IN TMUX")
    #     cmd = "js_shell 'j.servers.gedis.test_server_start()'"
    #     j.tools.tmux.execute(
    #         cmd,
    #         window='gedis_test',
    #         pane='main',
    #         reset=True,
    #     )

    #     res = j.sal.nettools.waitConnectionTest("localhost", int(gedis.config.data["port"]), timeoutTotal=1000)
    #     if not res:
    #         raise RuntimeError("Could not start gedis server on port:%s" % int(gedis.config.data["port"]))
    #     self.logger.info("gedis server '%s' started" % gedis.instance)
    #     print("[*] testing echo")

    #     cl = gedis.client_get(namespace="gedis_examples")
    #     assert cl.gedis_examples.echo("s") == b"s"
    #     print("- done")
    #     print("[*] testing set with schemas")
    #     # print("[1] schema_in as schema url")
    #     #
    #     # wallet_out1 = cl.gedis_examples.example1(addr="testaddr")
    #     # assert wallet_out1.addr == "testaddr"
    #     # print("[1] Done")
    #     print("[2] schema_in as inline schema with url")
    #     wallet_schema = j.data.schema.get("jumpscale.example.wallet")
    #     wallet_in = wallet_schema.new()
    #     wallet_in.addr = "testaddr"
    #     wallet_in.jwt = "testjwt"
    #     wallet_out = cl.gedis_examples.example2(wallet_in)

    #     assert wallet_in.addr == wallet_out.addr
    #     assert wallet_in.jwt == wallet_out.jwt
    #     print("[2] Done")

    #     print("[3] inline schema in and inline schema out")
    #     res = cl.gedis_examples.example3(a='a', b=True, c='2')
    #     assert res.a == 'a'
    #     assert res.b is True
    #     assert res.c == 2

    #     print("[3] Done")
    #     print("[4] inline schema for schema out with url")
    #     res = cl.gedis_examples.example4(wallet_in)
    #     assert res.result.addr == wallet_in.addr
    #     assert res.custom == "custom"
    #     print("[4] Done")

    #     s = j.clients.gedis.configure("system", port=cl.config.data["port"], namespace="system", secret="123456")

    #     assert s.system.ping().lower() == b"pong"

    #     print("**DONE**")
