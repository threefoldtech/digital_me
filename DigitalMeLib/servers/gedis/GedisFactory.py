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

    def _cmds_get(self, namespace, capnpbin):
        """
        Used in client only, starts from capnpbin (python client)
        """
        return GedisCmds(namespace=namespace, capnpbin=capnpbin)

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
        db = j.data.bcdb.get(zdb_cl)
        path = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/digital_me/tree/development_simple/packages/examples/models")
        j.data.bcdb.latest.models_add(path)


        path = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/digital_me/tree/development_simple/packages/examples/actors")
        gedis.cmds_add("orderbook", path+"/order_book_example.py")

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

        cl = gedis.client_get()

        j.shell()



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

