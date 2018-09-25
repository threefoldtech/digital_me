from Jumpscale import j
from .CapacityPlanner import CapacityPlanner

JSBASE = j.application.JSBaseClass


class Models:
    pass


class FarmerFactory(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.tools.threefold_farmer"
        JSBASE.__init__(self)
        self.zerotier_client = j.clients.zerotier.get("sysadmin")
        self.zerotier_net_sysadmin = self.zerotier_client.network_get(
                        "1d71939404587f3c")  # don't change the nr is fixed
        # self.zerotier_net_tfgrid = self.zerotier_client.network_get("") #TODO:*1
        self.iyo = j.clients.itsyouonline.get()
        self.jwt = self.iyo.jwt_get(refreshable=True, scope='user:memberof:threefold.sysadmin')
        self.capacity_planner = CapacityPlanner()
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
            self.bcdb.models_add(models_path, overwrite=True)
            self._models = Models()
            self._models.nodes = self.bcdb.model_get("threefold.grid.node")
            self._models.farmers = self.bcdb.model_get("threefold.grid.farmer")
            self._models.reservations = self.bcdb.model_get("threefold.grid.reservation")
            self._models.threebots = self.bcdb.model_get("threefold.grid.threebot")
            self.capacity_planner.models = self._models
        return self._models

    @property
    def nodes_active_sysadmin_nr(self):
        """
        how many nodes with ZOS have been found in sysadmin network
        :return:
        """
        nr_zos_sysadmin = len(self.models.index.select().where(self.models.index.up_zos is True))
        print("Found nr of nodes which can be managed over ZOS:%s" % nr_zos_sysadmin)
        return nr_zos_sysadmin

    @staticmethod
    def _tf_dir_node_find(ipaddr=None,id=None):
        for item in j.clients.threefold_directory.capacity:
            if ipaddr !=None and "robot_address" in item and ipaddr in item["robot_address"]:
                return item
            if id !=None and id.lower() == item['node_id'].lower():
                return item

    @staticmethod
    def _ping(ipaddr):
        """

        :param ipaddr:
        :return: empty string if ping was ok
        """
        active = False
        counter = 0
        error = ""
        while not active and counter < 4:
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

    def node_check(self, node, reset=False):
        """
        will do ping test, zero-os test, ...

        j.tools.threefold_farmer.node_check(10)

        :param node: node from model threefold.grid.node
        :return: the populated node obj
        """

        self._fail_save()

        if j.data.types.int.check(node):
            o = self.models.nodes.get(node)
        else:
            o = node


        if  o.update>j.data.time.epoch-3600 and reset==False:
            print("NOT NEEDED TO UPDATE:")
            print(o)
            return

        o.sysadmin = False
        o.error = ""
        o.noderobot = False
        o.sysadmin_up_ping = False
        o.sysadmin_up_zos = False
        o.tfdir_found = False
        o.tfgrid_up_ping = False

        ipaddr = o.sysadmin_ipaddr

        # PING TEST on sysadmin network
        error = self._ping(ipaddr)
        sysadmin_ping = error == ""

        # ZOSCLIENT
        zos = None
        if sysadmin_ping:
            try:
                zos = j.clients.zos.get(data={"password_": self.jwt, "host": ipaddr},
                                        instance="sysadmin_%s" % ipaddr)
            except Exception as e:
                if "Connection refused" in str(e):
                    error = "connection refused zosclient"
                else:
                    error = str(e)

        zos_ping = False
        if zos != None:
            try:
                zos_ping = "PONG" in zos.client.ping()
                o.sysadmin_up_last = j.data.time.epoch
                o.sysadmin_up_zos = j.data.time.epoch
            except Exception as e:
                if "Connection refused" in str(e):
                    zos_ping = False
                    error = "connection refused ping"
                else:
                    error = str(e)


        dir_item = self._tf_dir_node_find(ipaddr)
        if dir_item != None and zos != None:
            dir_item = self._tf_dir_node_find(id=zos.name)

        if sysadmin_ping and zos_ping:
            o.sysadmin = True
            o.node_zos_id = zos.name#zos.client.info.os()['hostid']



        o.sysadmin_up_ping = sysadmin_ping
        o.sysadmin_up_zos = zos_ping
        if o.error is not "zerotier lost the connection to the node":
            o.error = error


        if dir_item is not None:
            o.capacity_reserved.cru = dir_item["reserved_resources"]["cru"]
            o.capacity_reserved.hru = dir_item["reserved_resources"]["hru"]
            o.capacity_reserved.mru = dir_item["reserved_resources"]["mru"]
            o.capacity_reserved.sru = dir_item["reserved_resources"]["sru"]

            o.capacity_total.cru = dir_item["total_resources"]["cru"]
            o.capacity_total.hru = dir_item["total_resources"]["hru"]
            o.capacity_total.mru = dir_item["total_resources"]["mru"]
            o.capacity_total.sru = dir_item["total_resources"]["sru"]

            o.capacity_used.cru = dir_item["used_resources"]["cru"]
            o.capacity_used.hru = dir_item["used_resources"]["hru"]
            o.capacity_used.mru = dir_item["used_resources"]["mru"]
            o.capacity_used.sru = dir_item["used_resources"]["sru"]

            o.tfdir_found = True

            o.tfdir_up_last = dir_item["updated"]

            o.noderobot_ipaddr = dir_item["robot_address"]

            farmer = self.farmer_get_from_dir(dir_item["farmer_id"], return_none_if_not_exist=True)
            if farmer != None:
                o.farmer_id = farmer.id
                o.farmer = True

            if "location" in dir_item:
                o.location.city = dir_item["location"]["city"]
                o.location.continent = dir_item["location"]["continent"]
                o.location.country = dir_item["location"]["country"]
                o.location.latitude = dir_item["location"]["latitude"]
                o.location.longitude = dir_item["location"]["longitude"]

        robot = self.robot_get(o)
        if robot != None:
            if len(robot.templates.uids.keys()) >0 :
                o.noderobot = True
                o.noderobot_up_last = j.data.time.epoch
                o.state = "OK"

        o.tfdir_up_last = ""
        o.tf_dir_found = dir_item is not None

        o.update = j.data.time.epoch  #last time this check was done

        o = self.models.nodes.set(o)

        print(o)

    def robot_get(self,node):
        """
        :param node:
        :return: robot connection for node (model) specified
        """
        if node.noderobot_ipaddr == "":
            return None
        j.clients.zrobot.get(instance=node.node_zos_id, data={"url": node.noderobot_ipaddr})
        robot = j.clients.zrobot.robots[node.node_zos_id]
        return robot

    def farmer_get_from_dir(self,name,return_none_if_not_exist=False):
        res = self.models.farmers.index.select().where(self.models.farmers.index.name == name).execute()
        if len(res) > 0:
            o = self.models.farmers.get(res[0].id)
        else:
            if return_none_if_not_exist:
                return
            o = self.models.farmers.new()
        return o

    def farmers_load(self):
        """
        will get all farmers from tf directory & load in BCDB
        """
        farmers = j.clients.threefold_directory.farmers
        for farmer in farmers:
            if "name" not in farmer:
                j.shell()
                w
            obj = self.farmer_get_from_dir(farmer["name"])
            obj.name = farmer["name"]
            for waladdr in farmer[ 'wallet_addresses']:
                if waladdr not in obj.wallets:
                    obj.wallets.append(waladdr)
            obj.iyo_org = farmer['iyo_organization']
            self.models.farmers.set(obj)

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

    def node_get_from_tfdir(self, node_host_id, return_none_if_not_exist=False):
        """
        get the node starting from tf directory property
        :param node_addr:
        :param return_none_if_not_exist:
        :return:
        """
        res = self.models.nodes.index.select().where(self.models.nodes.index.node_zos_id == node_host_id).execute()
        if len(res) > 0:
            o = self.models.nodes.get(res[0].id)
        else:
            if return_none_if_not_exist:
                return
            o = self.models.nodes.new()
        return o

    def zerotier_scan(self,reset=False):
        """
        will do a scan of the full zerotier sysadmin network, this can take a long time
        :return:

        js_shell 'j.tools.threefold_farmer.zerotier_scan()'

        """

        for node in self.zerotier_net_sysadmin.members_list():
            online = node.data["online"]  # online from zerotier
            online_past_sec = int(j.data.time.epoch - node.data["lastOnline"] / 1000)
            ipaddr = node.data["config"]["ipAssignments"][0]
            error = ""
            if online:
                o = self.node_get_from_zerotier(node.address)
                o.sysadmin_ipaddr = ipaddr
                o.node_zerotier_id = node.address
                self.node_check(o,reset=reset)
            else:
                o = self.node_get_from_zerotier(node.address, return_none_if_not_exist=True)
                if o is not None:
                    # means existed in DB
                    self.node_check(o,reset=reset)

    def tf_dir_scan(self,reset=False):
        """
        walk over all nodes found in tfdir
        do ping test over pub zerotier grid network
        :return:
        """
        for item in j.clients.threefold_directory.capacity:
            node = self.node_get_from_tfdir(item["node_id"])

            self.node_check(node, reset=reset)

    def _fail_save(self):
        if self._bcdb == None:
            self.zdb = j.clients.zdb.testdb_server_start_client_get(reset=False)
            self._bcdb = j.data.bcdb.get(self.zdb, reset=False)

    def load(self, reset=False):
        """
        load the info from different paths into database

        js_shell 'j.tools.threefold_farmer.load(reset=True)'

        :param reset:
        :return:
        """
        self.zdb = j.clients.zdb.testdb_server_start_client_get(reset=reset)
        self._bcdb = j.data.bcdb.get(self.zdb, reset=reset)  # to make sure we reset the index


        self.farmers_load()
        self.zerotier_scan(reset=reset)
        # self.tf_dir_scan(reset=reset)
