from Jumpscale import j

import gevent

from gevent import monkey
# from .Community import Community
from .ServerRack import ServerRack
from .Package import Package
import time
from gevent import event, sleep
import os
import socket
import netstr
import sys
import time
JSBASE = j.application.JSBaseClass


class DigitalMe(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.servers.digitalme"
        JSBASE.__init__(self)
        self.filemonitor = None
        # self.community = Community()
        self.packages= {}

    # def packages_add(self,path,zdbclients):
    #     """
    #
    #     :param path: path of packages, will look for dm_package.toml
    #     :return:
    #     """
    #     graphql_dir = ''
    #     for item in j.sal.fs.listFilesInDir(path, recursive=True, filter="dm_package.toml",
    #                             followSymlinks=False, listSymlinks=False):
    #         pdir = j.sal.fs.getDirName(item)
    #         # don't lopad now! defer as last package
    #         if pdir.endswith('graphql/'):
    #             graphql_dir = pdir
    #             continue
    #         self.package_add(pdir,zdbclients=zdbclients)
    #
    #     # load graphql as latest package.
    #     # this ensures all schemas are loaded, so auto generation of queries for all loaded schemas
    #     # can be acheieved!
    #     if graphql_dir:
    #         self.package_add(graphql_dir, zdbclients=zdbclients)
    #     # Generate js client code
    #     j.servers.gedis.latest.code_generate_webclient()

    def package_add(self,path,bcdb):
        """

        :param path: directory where there is a dm_package.toml inside = a package for digital me
        has blueprints, ...
        :return:
        """
        if not j.sal.fs.exists(path):
            raise j.exceptions.Input("could not find:%s"%path)
        p=Package(path_config=path,bcdb=bcdb)
        if p.name not in self.packages:
            self.packages[p.name]=p

    def _run_exec(self,cmd):
        #need better way to return the result, how to use the socket well???
        # https://github.com/jprjr/sockexec
        args = cmd.split(" ")
        path = "/sandbox/var/exec.sock"
        if not os.path.exists(path):
            raise RuntimeError("cannot find exec socket path:%s"%path)
        client = socket.socket(socket.AF_UNIX)
        client.connect(path)
        s=netstr.encode(str(len(args)).encode())
        for cmd in args:
            s+=netstr.encode(cmd.encode())
        s+=netstr.encode(b"")
        client.sendall(s)
        while True:
            r=client.recv(1024)
            if r!=b'':
                print(r.decode()) #doing line breaks, should not, also not using netstring for return, has too
            time.sleep(0.01)


    def _socket_check(self,path,msg=""):
        if os.path.exists(path):
            client = socket.socket(socket.AF_UNIX)
            client.connect(path)
            return True
        return False


    def start(self,secret,namespace="digitalme",restart=False,destroydata=False,zdbinternal=True):
        """
        js_shell 'j.servers.digitalme.start(secret="1234")'
        js_shell 'j.servers.digitalme.start(secret="1234",destroydata=True)'


        the secret is the real secret of your digitalme, it needs also an ssh-agent loaded
        the combination delivers all required security

        :param secret:
        :param namespace: is the namespace as used on ZDB
        :param destroydata: if used will remove all data before starting, be carefull
        :param restart, will restart the tmux
        :return:

        window in tmux: digitalme
        pannels in tmux:
           - 12 = redis
           - 13 = zdb
           - 14 = execsocket
           - 21 = openresty
           - 22 = digitalme

        """

        if restart:
            j.tools.panes_digitalme_create(reset=restart)

        #make sure we have redis running
        j.clients.redis.core_get()

        if restart or not j.sal.nettools.tcpPortConnectionTest("localhost",8081):
            j.servers.openresty.start()

        # #get sockexec to run
        if restart or not self._socket_check("/sandbox/var/exec.sock"):
            cmd = j.tools.tmux.cmd_get(name="runner",pane="p14",cmd="rm -f /sandbox/var/exec.sock;sockexec /sandbox/var/exec.sock")
            cmd.stop()
            cmd.start()


        secret = j.data.hash.md5_string(secret) #to make sure we don't have to store the secret as plain text somewhere

        self.nacl =  j.data.nacl.get(name="digitalme",secret=j.data.hash.md5_string(secret+"digitalme")) #just to make sure secret in nacl is not same as namespace

        if zdbinternal:
            j.servers.zdb.adminsecret =  self.nacl.ssh_hash(secret+"admin")
            j.servers.zdb.name = "digitalme"

            if destroydata or restart:
                j.servers.zdb.stop()
                zdbrunning = False
            else:
                zdbrunning = j.servers.zdb.isrunning()

            if not zdbrunning:
                j.servers.zdb.start(destroydata=destroydata)

            try:
                cladmin = j.servers.zdb.client_admin_get()
            except Exception as e:
                if str(e).find("Access denied")!=-1:
                    print("\nERROR:\n    cannot connect to ZDB, admin secret different, restart without ZDB init or destroy ZDB data\n")
                    sys.exit(1)
                raise e

            if not cladmin.namespace_exists(namespace):
                secretns = self.nacl.ssh_hash(namespace+secret)  #will generate a unique hash which will only be relevant when right ssh-agent loaded
                zdbcl = cladmin.namespace_new(namespace, secret=secretns, maxsize=0, die=True)

        # self._run_exec("find /")
        # j.shell()
        # ws


        # def install_zrobot():
        #     path = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/0-robot")
        #     j.sal.process.execute("cd %s;pip3 install -e ." % path)
        #
        # if "_zrobot" not in j.servers.__dict__.keys():
        #     # means not installed yet
        #     install_zrobot()



        env={}
        env["addr"]="localhost"
        env["port"]="9900"
        env["namespace"]=namespace
        env["secret"]=secret
        cmd_="js_shell 'j.servers.digitalme.start_from_zdb()'"
        cmd = j.tools.tmux.cmd_get(name="digitalme",pane="p22",cmd=cmd_, env=env,process_strings=[])

        cmd.stop()
        cmd.start()




        gedisclient = j.clients.gedis.configure(namespace,namespace="system",port=8001,secret=secret,host="localhost")

        assert gedisclient.system.ping() == b"PONG"

        return gedisclient





    def start_from_zdb(self, addr="localhost",port=9900,namespace="digitalme", secret="1234"):
        """

        examples:

        js_shell 'j.servers.digitalme.start_from_zdb()'

        :param addr: addr of starting zerodb namespace
        :param port: port
        :param namespace: name of the namespace
        :param secret: the secret of the namespace

        can also pass the arguments as env variables

        :return:




        """

        if "addr" in os.environ:
            addr = os.environ["addr"]
        if "port" in os.environ:
            port = int(os.environ["port"])
        if "namespace" in os.environ:
            namespace = os.environ["namespace"]
        if "secret" in os.environ:
            secret = os.environ["secret"]

        if len(secret)!=32:
            secret = j.data.hash.md5_string(secret)


        self.nacl =  j.data.nacl.get(name="digitalme",secret=j.data.hash.md5_string(secret+"digitalme")) #just to make sure secret in nacl is not same as namespace

        secretns = self.nacl.ssh_hash(namespace+secret)  #will generate a unique hash which will only be relevant when right ssh-agent loaded

        self.zdbclient = j.clients.zdb.client_get(nsname=namespace, addr=addr, port=port, secret=secretns, mode='seq')

        self.rack = self.server_rack_get()

        geventserver = j.servers.gedis.configure(host="localhost", port="8001", ssl=False,
                                  adminsecret=secret, instance=namespace)

        self.rack.add("gedis", geventserver.redis_server) #important to do like this, otherwise 2 servers started

        key = "%s_%s_%s"%(addr,port,namespace)
        self.bcdb = j.data.bcdb.new("digitalme_%s"%key, zdbclient=self.zdbclient, cache=True)

        self.web_reload()

        self.rack.start()



    def web_reload(self):

        #add configuration to openresty

        j.servers.openresty.configs_add(j.sal.fs.joinPaths(self._dirpath,"web_config"),args={"staticpath":staticpath})


        bcdb = self.bcdb

        #the core packages, always need to be loaded
        toml_path = j.clients.git.getContentPathFromURLorPath(
                "https://github.com/threefoldtech/digital_me/tree/development960/packages/system/base")
        self.package_add(toml_path,bcdb=bcdb)
        toml_path = j.clients.git.getContentPathFromURLorPath(
                "https://github.com/threefoldtech/digital_me/tree/development960/packages/system/chat")
        self.package_add(toml_path,bcdb=bcdb)
        toml_path = j.clients.git.getContentPathFromURLorPath(
                "https://github.com/threefoldtech/digital_me/tree/development960/packages/system/example")
        self.package_add(toml_path,bcdb=bcdb)



    def server_rack_get(self):

        """
        returns a server rack

        to start the server manually do:
        js_shell 'j.servers.digitalme.start(namespace="test", secret="1234")'

        """

        return ServerRack()


    def test(self,manual=False):
        """
        js_shell 'j.servers.digitalme.test()'
        js_shell 'j.servers.digitalme.test(manual=True)'

        :param manual means the server is run manually using e.g. js_shell 'j.servers.digitalme.start()'

        """

        admincl = j.clients.zdb.testdb_server_start_client_admin_get()  # starts & resets a zdb in seq mode with name test
        cl = admincl.namespace_new("test",secret="1234")

        if manual:
            namespace="system"
            #if server manually started can use this
            secret="1234"
            gedisclient = j.clients.gedis.configure(namespace,namespace=namespace,port=8001,secret=secret,
                                                        host="localhost")
        else:
            #gclient will be gedis client
            gedisclient = self.start(addr=cl.addr,port=cl.port,namespace=cl.nsname, secret=cl.secret,background=True)

        # ns=gedisclient.core.namespaces()
        j.shell()

