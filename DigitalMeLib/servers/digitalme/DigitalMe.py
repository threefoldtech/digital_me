from .ServerRack import ServerRack
from .Package import Package
from Jumpscale import j

JSBASE = j.application.JSBaseClass


class DigitalMe(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.servers.digitalme"
        JSBASE.__init__(self)
        self.filemonitor = None
        self.packages = {}
        self._bcdb = None

    @property
    def bcdb(self):
        if self._bcdb:
            return self._bcdb
        raise ValueError("bcdb not initialized yet")

    def package_add(self, path):
        """
        :param path: the package path
        :type path: string
        """
        if path.startswith("https"):
            path = j.clients.git.getContentPathFromURLorPath(path)

        if not j.sal.fs.exists(path):
            raise j.exceptions.Input("could not find:%s" % path)

        p = Package(path_config=path, bcdb=self.bcdb)
        if p.name not in self.packages:
            self.packages[p.name] = p

    def start(self, addr="localhost", port=9900, namespace="digitalme", secret="1234", background=False):
        """
        examples:

        js_shell 'j.servers.digitalme.start()'
        js_shell 'j.servers.digitalme.start(addr="localhost",port=9900,namespace="digitalme", secret="1234")'

        :param addr: addr of starting zerodb namespace
        :type addr: string
        :param port: port zerodb is listening on
        :type port: int
        :param namespace: name of the namespace
        :type namespace: string
        :param secret: the secret of the namespace
        :type secret: string
        :param background: boolean indicating whether the server will run in the background or not
        :type background: bool
        """

        def install_zrobot():
            path = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/0-robot")
            j.sal.process.execute("cd %s;pip3 install -e ." % path)

        if "_zrobot" not in j.servers.__dict__.keys():
            # means not installed yet
            install_zrobot()

        if background:

            cmd = "js_shell 'j.servers.digitalme.start(addr=\"%s\",port=%s,namespace=\"%s\", secret=\"%s\")'" %\
                  (addr, port, namespace, secret)

            process_strings = ["j.servers.digitalme.start"]

            p = j.tools.tmux.execute(name="digitalme",
                                     cmd=cmd, reset=True, window="digitalme")
        else:
            self.rack = self.server_rack_get()
            geventserver = j.servers.gedis.configure(host="localhost", port="8001", ssl=False,
                                                     adminsecret=secret, instance=namespace)
            self.rack.add("gedis", geventserver.redis_server)  # important to do like this, otherwise 2 servers started
            zdbclient = j.clients.zdb.client_get(nsname=namespace, addr=addr, port=port, secret=secret, mode='seq')
            key = "%s_%s_%s" % (addr, port, namespace)
            self._bcdb = j.data.bcdb.new("digitalme_%s" % key, zdbclient=zdbclient, cache=True)
            self.web_reload()
            self.rack.start()

    def web_reload(self):
        """Reload digital me packages and openresty configs
        """
        # add configuration to openresty
        staticpath = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldtech/jumpscale_weblibs/tree/master/static")

        j.servers.openresty.configs_add(j.sal.fs.joinPaths(
            self._dirpath, "web_config"), args={"staticpath": staticpath})

        # the core packages, always need to be loaded
        self.package_add("https://github.com/threefoldtech/digital_me/tree/development960/packages/system/base")
        self.package_add("https://github.com/threefoldtech/digital_me/tree/development960/packages/system/chat")
        self.package_add("https://github.com/threefoldtech/digital_me/tree/development960/packages/system/example")

        # j.servers.openresty.start()
        # j.servers.openresty.reload()

    def server_rack_get(self):
        """
        returns a server rack

        to start the server manually do:
        js_shell 'j.servers.digitalme.start(namespace="test", secret="1234")'

        """
        return ServerRack()

    def test(self, manual=False):
        """
        js_shell 'j.servers.digitalme.test()'
        js_shell 'j.servers.digitalme.test(manual=True)'

        :param manual means the server is run manually using e.g. js_shell 'j.servers.digitalme.start()'
        """

        # Starts & resets a zdb in seq mode with name test
        admincl = j.clients.zdb.testdb_server_start_client_admin_get()
        cl = admincl.namespace_new("test", secret="1234")

        if manual:
            namespace = "system"
            # if server manually started can use this
            secret = "1234"
            gedisclient = j.clients.gedis.configure(namespace, namespace=namespace, port=8001, secret=secret,
                                                    host="localhost")
        else:
            # gclient will be gedis client
            gedisclient = self.start(addr=cl.addr, port=cl.port, namespace=cl.nsname, secret=cl.secret, background=True)

        # ns=gedisclient.core.namespaces()
        j.shell()
