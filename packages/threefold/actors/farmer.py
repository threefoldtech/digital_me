from Jumpscale import j
JSBASE = j.application.JSBaseClass


class farmer(JSBASE):
    """
    This class functions are actually registered in

    """
    def __init__(self):
        JSBASE.__init__(self)

        # IN CASE YOU NEED TO CONFIGURE
        # zt.config.data={"token_":"..."}
        # zt.config.save()

        self.sysadmin_net = zt.network_get("1d71939404587f3c")
        self.iyo = j.clients.itsyouonline.get()
        self.jwt = iyo.jwt_get(refreshable=True, scope='user:memberof:threefold.sysadmin')
        j.shell()
        url="threefold.grid.node"
        self.model



    def nodes_active_sysadmin_nr(self):
        """
        how many nodes with ZOS have been found in sysadmin network
        :return:
        """
        nr_zos_sysadmin = len(self.model.index.select().where(self.model.index.up_zos == True))
        print("Found nr of nodes which can be managed over ZOS:%s" % nr_zos_sysadmin)

    def _tf_dir_node_find(self,ipaddr):
        for item in j.clients.threefold_directory.capacity:
            if ipaddr in item["robot_address"]:
                return item

    def _node_check(self,o):

        error = ""
        ipaddr = o.ipaddr

        #PING TEST
        active = False
        counter = 0
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

        #ZOSCLIENT
        zos=None
        if active:
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

        dir_item = tf_dir_node_find(ipaddr)


        if zos_ping:
            o.sysadmin = True
            o.node_zos_hostid = zos.client.info.os()['hostid']
        o.up_ping = active
        o.up_zos = zos_ping
        if o.error is not "zerotier lost the connection to the node":
            o.error = error
        o.tf_dir_found = dir_item is not None
        o = self.model.set(o)

        print(o)


    def _node_get(self,node_addr,return_none_if_not_exist=False):
        res = self.model.index.select().where(self.model.index.node_zt_id == node_addr).execute()
        if len(res) > 0:
            o = self.model.get(res[0].id)
        else:
            if return_none_if_not_exist:
                return
            o = self.model.new()
        return o


    def zerotier_scan(self):
        """
        will schedule a scan of the full zerotier sysadmin network, this can take a long time
        :return:
        """

        for node in self.sysadmin_net.members_list():
            online = node.data["online"]
            online_past_sec = int(j.data.time.epoch - node.data["lastOnline"] / 1000)
            ipaddr=node.data["config"]["ipAssignments"][0]
            error = ""
            if online:
                o = node_get(node.address)
                o.ipaddr = ipaddr
                o.node_zt_id = node.address
                o.up_zerotier = True
                node_check(o)
            else:
                o = node_get(node.address,return_none_if_not_exist=True)
                if o is not None:
                    #means existed in DB
                    o.up_zerotier = False
                    o.up_ping = False
                    o.up_zos = False
                    o.error="zerotier lost the connection to the node"
                    node_check(o)