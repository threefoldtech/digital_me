from Jumpscale import j
from .CapacityPlanner import CapacityPlanner
JSBASE = j.application.JSBaseClass

class Models():
    pass

class FarmerFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.tools.threefold_farmer"
        JSBASE.__init__(self)
        self.zerotier_client = j.clients.zerotier.get("sysadmin")
        self.zerotier_net_sysadmin = self.zerotier_client.network_get("1d71939404587f3c") #don't change the nr is fixed
        # self.zerotier_net_tfgrid = self.zerotier_client.network_get("") #TODO:*1
        self.iyo = j.clients.itsyouonline.get()
        self.jwt = self.iyo.jwt_get(refreshable=True, scope='user:memberof:threefold.sysadmin')
        self.capacityplanner = CapacityPlanner()
        self.zdb = None
        self._models = None
        self._bcdb = None


    @property
    def bcdb(self):
        if self.zdb is None:
            raise RuntimeError("you need to set self.zdb with a zerodb connection")
        if self._bcdb is None:
            self._bcdb = j.data.bcdb.get(self.zdb)
        return self._bcdb

    @property
    def models(self):
        if self.zdb is None:
            raise RuntimeError("you need to set self.zdb with a zerodb connection")
        if self._models is None:
            models_path = j.clients.git.getContentPathFromURLorPath(
                "https://github.com/threefoldtech/digital_me/tree/development_simple/packages/threefold/models")
            self.bcdb.models_add(models_path,overwrite=True)
            self._models = Models()
            self._models.nodes = self.bcdb.model_get("threefold.grid.node")
            self._models.farmers = self.bcdb.model_get("threefold.grid.farmer")
            self._models.reservations = self.bcdb.model_get("threefold.grid.reservation")
            self._models.threebots = self.bcdb.model_get("threefold.grid.threebot")
        return self._models


    @property
    def nodes_active_sysadmin_nr(self):
        """
        how many nodes with ZOS have been found in sysadmin network
        :return:
        """
        nr_zos_sysadmin = len(self.models.index.select().where(self.models.index.up_zos == True))
        print("Found nr of nodes which can be managed over ZOS:%s" % nr_zos_sysadmin)

    def _tf_dir_node_find(self, ipaddr):
        for item in j.clients.threefold_directory.capacity:
            if ipaddr in item["robot_address"]:
                return item

    def _ping(self,ipaddr):
        """

        :param ipaddr:
        :return: empty string if ping was ok
        """
        active = False
        counter = 0
        error = ""
        while active == False and counter < 4:
            try:
                active = j.sal.nettools.pingMachine(ipaddr)
            except Exception as e:
                if "packet loss" in str(e):
                    print("ping fail for:%s" % ipaddr)
                    counter += 1
                    error = "packet loss"
                else:
                    error = str(e)
        return error

    def node_check(self, node):
        """
        will do ping test, zero-os test, ...

        :param node: node from model threefold.grid.node
        :return: the populated node obj
        """

        if j.data.types.int.check(node):
            o = self.models.nodes.get(nodeid)
        else:
            o = node


        o.sysadmin = False
        o.error = ""
        o.noderobot = False
        o.sysadmin_up_ping = False
        o.sysadmin_up_zos = False
        o.tfdir_found = False
        o.tfgrid_up_ping = False

        ipaddr = o.sysadmin_ipaddr

        #PING TEST on sysadmin network
        error = self._ping(ipaddr)
        sysadmin_ping = error == ""


        #ZOSCLIENT
        zos=None
        if sysadmin_ping:
            try:
                zos = j.clients.zos.get(data={"password_": jwt, "host": ipaddr},
                                        instance="sysadmin_%s" % ipaddr)
            except Exception as e:
                if "Connection refused" in str(e):
                    error = "connection refused zosclient"
                else:
                    error = str(e)

        zos_ping = False
        if zos is not None:
            try:
                zos_ping = "PONG" in zos.client.ping()
            except Exception as e:
                if "Connection refused" in str(e):
                    zos_ping = False
                    error = "connection refused ping"
                else:
                    error = str(e)

        dir_item = self._tf_dir_node_find(ipaddr)
        if dir_item is not None:
            j.shell()
            w


        if sysadmin_ping and zos_ping:
            o.sysadmin = True
            o.node_zos_id = zos.client.info.os()['hostid']
        o.sysadmin_up_ping = sysadmin_ping
        o.sysadmin_up_zos = zos_ping
        if o.error is not "zerotier lost the connection to the node":
            o.error = error
        #TODO:*1 need to set the uptimes...
        j.shell()
        o.tfdir_up_last = ""
        o.tf_dir_found = dir_item is not None
        o = self.models.set(o)

        print(o)


    def node_get_from_zerotier(self, node_addr, return_none_if_not_exist=False):
        """
        get the node starting from address in zerotier
        :param node_addr:
        :param return_none_if_not_exist:
        :return:
        """
        res = self.models.nodes.index.select().where(self.models.nodes.index.node_zerotier_id == node_addr).execute()
        if len(res) > 0:
            o = self.models.nodes.get(res[0].id)
        else:
            if return_none_if_not_exist:
                return
            o = self.models.nodes.new()
        return o


    def zerotier_scan(self):
        """
        will do a scan of the full zerotier sysadmin network, this can take a long time
        :return:

        js_shell 'j.tools.threefold_farmer.zerotier_scan()'

        """

        for node in self.zerotier_net_sysadmin.members_list():
            online = node.data["online"] #online from zerotier
            online_past_sec = int(j.data.time.epoch - node.data["lastOnline"] / 1000)
            ipaddr=node.data["config"]["ipAssignments"][0]
            error = ""
            if online:
                o = self.node_get_from_zerotier(node.address)
                o.sysadmin_ipaddr = ipaddr
                o.node_zerotier_id = node.address
                self.node_check(o)
            else:
                o = node_get_from_zerotier(node.address,return_none_if_not_exist=True)
                if o is not None:
                    #means existed in DB
                    self.node_check(o)

    def tfdir_scan(self):
        """
        walk over all nodes found in tfdir
        do ping test over pub zerotier grid network
        :return:
        """
        #TODO:*1


    def test(self, reset=False):
        """
        js_shell 'j.tools.threefold_farmer.test(reset=True)'

        :param reset:
        :return:
        """
        self.reset=reset
        self.zdb = j.clients.zdb.testdb_server_start_client_get(reset=reset)
        self._bcdb = j.data.bcdb.get(self.zdb,reset=reset) #to make sure we reset the index
        self.zerotier_scan()


