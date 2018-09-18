import os

from Jumpscale import j

from .GedisServer import GedisServer
from .GedisCmds import GedisCmds
from .GedisChatBot import GedisChatBotFactory

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
        if data is None:
            data = {}

        return super(GedisFactory, self).get(instance=instance, data=data, interactive=interactive)        


    def geventserver_get(self, instance=""):
        """
        return redis_server
        """
        server = self.get(instance=instance)
        return server.redis_server

    def configure(
            self,
            instance="test",
            port=8889,
            host="localhost",
            ssl=False,
            adminsecret="",
            interactive=False,
            configureclient=True
    ):

        data = {
            "port": str(port),
            "host": host,
            "adminsecret_": adminsecret,
            "ssl": ssl,
        }

        if configureclient:
            j.clients.gedis.configure(instance=instance,
                                      host=host, port=port, secret=adminsecret, ssl=ssl, reset=True, get=False)

        server=self.get(instance, data, interactive=interactive)
        server.client_configure() #configures the client
        return server

    def _cmds_get(self, key, capnpbin):
        """
        Used in client only, starts from capnpbin (python client)
        """
        namespace, name = key.split("__")
        return GedisCmds(namespace=namespace,name=name, capnpbin=capnpbin)

    @property
    def path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__))

    def test_server_start(self):
        """
        this method is only used when not used in digitalme
        js_shell 'j.servers.gedis.test_server_start()'

        """

        gedis = self.get(instance="test")

        zdb_cl = j.clients.zdb.testdb_server_start_client_get(reset=False)
        bcdb = j.data.bcdb.get(zdb_cl,namespace="test")
        path = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/digital_me/tree/development_simple/packages/examples/models")
        bcdb.models_add(path=path)


        path = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/digital_me/tree/development_simple/packages/examples/actors")
        gedis.actors_add(namespace="gedis_examples", path=path)
        gedis.models_add(namespace="gedis_examples", models=bcdb)

        gedis.start()



    def test(self,zdb_start=True):
        """
        js_shell 'j.servers.gedis.test(zdb_start=False)'
        """

        if zdb_start:
            # remove configuration of the gedis factory
            self.delete("test")
            cl = j.clients.zdb.testdb_server_start_client_get(reset=True)

        gedis = self.configure(instance="test", port=8888, host="localhost", ssl=False,
                               adminsecret="1234", interactive=False)

        print("START GEDIS IN TMUX")
        cmd = "js_shell 'j.servers.gedis.test_server_start()'"
        j.tools.tmux.execute(
            cmd,
            session='main',
            window='gedis_test',
            pane='main',
            session_reset=False,
            window_reset=True
        )

        res = j.sal.nettools.waitConnectionTest("localhost", int(gedis.config.data["port"]), timeoutTotal=1000)
        if res == False:
            raise RuntimeError("Could not start gedis server on port:%s" % int(gedis.config.data["port"]))
        self.logger.info("gedis server '%s' started" % gedis.instance)
        print("[*] testing echo")
<<<<<<< HEAD
        cl = gedis.client_get(namespace="orderbook")
        assert cl.order_book.echo("s") == b"s"
        print("- done")
        print("[*] testing wallet set with schemas")
        wallet = cl.order_book.wallet_set(addr="testaddr", jwt="testjwt")

        assert wallet.addr == "testaddr"
        assert wallet.jwt == "testjwt"

        j.shell()

=======
        cl = gedis.client_get(namespace="gedis_examples")
        assert cl.gedis_examples.echo("s") == b"s"
>>>>>>> 3c62ad25c10ba47ba177cf64f08dbc9354b3f911
        print("- done")
        print("[*] testing set with schemas")
        print("[1] schema_in as schema url")

        wallet_out1 = cl.gedis_examples.example1(addr="testaddr")
        assert wallet_out1.addr == "testaddr"
        print("[1] Done")
        print("[2] schema_in as inline schema with url")
        wallet_schema = j.data.schema.schema_get("jumpscale.example.wallet")
        wallet_in = wallet_schema.new()
        wallet_in.addr = "testaddr"
        wallet_in.jwt = "testjwt"
        wallet_out = cl.gedis_examples.example2(wallet_in)

        assert wallet_in.addr == wallet_out.addr
        assert wallet_in.jwt == wallet_out.jwt
        print("[2] Done")

        print("[3] inline schema in and inline schema out")
        res = cl.gedis_examples.example3(a='a', b=True, c='2')
        assert res.a == 'a'
        assert res.b is True
        assert res.c == 2

        print("[3] Done")
        print("[4] inline schema for schema out with url")
        res = cl.gedis_examples.example4(wallet_in)
        assert res.result.addr == wallet_in.addr
        assert res.custom == "custom"
        print("[4] Done")

        print("**DONE**")


    # def chatbot_test(self):
    #     """
    #     js_shell 'j.servers.gedis.chatbot_test()'
    #     """
    #     bot = GedisChatBotFactory()
    #     bot.test()
    #     #TODO:*1 not working

#     def new(
#             self,
#             instance="test",
#             port=8889,
#             host="localhost",
#             ssl=False,
#             adminsecret="",
# ]        ):
#         """
#         creates new server on path, if not specified will be current path
#         will start from example app
#
#         js_shell 'j.servers.gedis.new(path="{{DIRS.TMPDIR}}/jumpscale/gedisapp/",reset=True)'
#
#         """
#
#         if path == "":
#             path = j.sal.fs.getcwd()
#         else:
#             path = j.tools.jinja2.text_render(path)
#
#         if reset:
#             j.sal.fs.removeDirTree(path)
#
#         if j.sal.fs.exists("%s/actors" % path) or j.sal.fs.exists("%s/schema" % path):
#             raise RuntimeError("cannot do new app because app or schema dir does exist.")
#
#         # src = j.clients.git.getContentPathFromURLorPath(
#         #     "https://github.com/threefoldtech/jumpscale_lib/tree/development/apps/template")
#         # dest = path
#         # self.logger.info("copy templates to:%s" % dest)
#
#         gedis = self.configure(instance=instance, port=port, host=host, ssl=ssl, adminsecret=adminsecret)
#
#         # j.tools.jinja2.copy_dir_render(src, dest, reset=reset, j=j, name="aname", config=gedis.config.data,
#         #                                instance=instance)
#
#         self.logger.info("gedis app now in: '%s'\n    do:\n    cd %s;sh start.sh" % (dest, dest))

