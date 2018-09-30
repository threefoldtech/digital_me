from Jumpscale import j
JSBASE = j.application.JSBaseClass


class farmer(JSBASE):
    """
    This class functions are actually registered in

    """
    def __init__(self):
        JSBASE.__init__(self)
        j.tools.threefold_farmer.zdb = j.clients.zdb.testdb_server_start_client_get(reset=False)
        self._bcdb = j.tools.threefold_farmer.bcdb
        self._farmer_model = None
        self._node_model = None
        self._wgw_model = None
        self.capacity_planner = j.tools.threefold_farmer.capacity_planner

    @property
    def farmer_model(self):
        if not self._farmer_model:
            self._farmer_model = self._bcdb.model_get('threefold.grid.farmer')
        return self._farmer_model

    
    @property
    def node_model(self):
        if not self._node_model:
            self._node_model = self._bcdb.model_get('threefold.grid.node')
        return self._node_model

    @property
    def wgw_model(self):
        if not self._wgw_model:
            self._wgw_model = self._bcdb.model_get('threefold.grid.webgateway')
        return self._wgw_model

    def farmers_get(self):
        """
        :return: [farmer_obj]
        """
        return self.farmer_model.get_all()

    def country_list(self):
        """
        :return: list of countries
        """
        nodes = self.node_model.get_all()
        result = {n.location.country for n in nodes}
        if '' in result:
            result.remove('')
        return list(result)

    def node_find(self, country="", farmer_name="", cores_min_nr=0, mem_min_mb=0, ssd_min_gb=0, hd_min_gb=0, nr_max=10):
        """
        the capacity checked against is for free (available) capacity (total-used)

        :param country:
        :param farmer_name:
        :param cores_min_nr:
        :param mem_min_mb:
        :param ssd_min_gb:
        :param hd_min_gb:
        :param nr_max: max nr of records to return

        :return: [node_objects]

        """
        nodes = self.node_model.get_all()
        if country:
            nodes = list(filter(lambda x: x.location.country == country, nodes))
        if farmer_name:
            farmers = self.farmers_get()
            farmer_id = [farmer.id for farmer in farmers if farmer.name == farmer_name]
            nodes = list(filter(lambda x: x.farmer_id == farmer_id, nodes))
        if cores_min_nr:
            nodes = list(filter(lambda x: x.capacity_total.cru > cores_min_nr, nodes))
        if mem_min_mb:
            nodes = list(filter(lambda x: x.capacity_total.mru > mem_min_mb, nodes))
        if ssd_min_gb:
            nodes = list(filter(lambda x: x.capacity_total.sru > ssd_min_gb, nodes))
        if hd_min_gb:
            nodes = list(filter(lambda x: x.capacity_total.hru > hd_min_gb, nodes))

        if nr_max:
            nodes = nodes[:nr_max]
        return nodes


    def zos_reserve(self, jwttoken, node_id, vm_name, memory=1024, cores=1, zerotier_network="", adminsecret=""):
        """

        deploys a zero-os for a customer

        :param node_id: is the id of the node on which you want to deploy
        :param vm_name: name freely chosen by customer
        :param memory: Amount of memory in MiB (defaults to 1024)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param zerotier_network: is optional additional network to connect to
        :param adminsecret: is the secret which is set on the redis for the ZOS of the customer

        :return: (node_robot_url, servicesecret, ipaddr_zos,redisport)

        user can now connect the ZOS client to this ipaddress with specified adminsecret over SSL

        each of these ZOS'es is automatically connected to the TF Public Zerotier network (TODO: which one is it)

        ZOS is only connected to the 1 or 2 zerotier networks ! and NAT connection to internet.

        """
        node_robot_url, service_secret, ipaddr_zos, redis_port = self.capacity_planner.zos_reserve(node_id,
                            vm_name, memory=memory, cores=cores, zerotier_network=zerotier_network, organization="")
        return (node_robot_url, service_secret, ipaddr_zos, redis_port)

    def ubuntu_reserve(self, jwttoken, node_id, vm_name, memory=2048, cores=2, zerotier_network="", zerotier_token="", pub_ssh_key=""):
        """

        deploys a ubuntu 18.04 for a customer on a chosen node

        :param node_id: is the id of the node on which you want to deploy
        :param vm_name: name freely chosen by customer
        :param memory: Amount of memory in MiB (defaults to 1024)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param zerotier_network: is optional additional network to connect to
        :param pub_ssh_key: is the pub key for SSH authorization of the VM

        :return: (node_robot_url, servicesecret,ipaddr_vm)

        user can now connect to this ubuntu over SSH, port 22 (always), only on the 2 zerotiers

        each of these VM's is automatically connected to the TF Public Zerotier network (TODO: which one is it)

        VM is only connected to the 1 or 2 zerotier networks ! and NAT connection to internet.

        """
        node_robot_url, service_secret, ipaddr_vm = self.capacity_planner.ubuntu_reserve(node_id,
                    vm_name, memory=memory, cores=cores, zerotier_network=zerotier_network, zerotier_token=zerotier_token, pub_ssh_key=pub_ssh_key)
        return (node_robot_url, service_secret, ipaddr_vm)

    def zdb_reserve(self, jwttoken, node_id, name_space, size=100, secret=""):
        """
        :param node_id: is the id of the node on which you want to deploy
        :param size:  in MB
        :param secret: secret to be given to the namespace
        :param name_space: cannot exist yet
        :return: (node_robot_url, servicesecret, ipaddr, port)

        user can now connect to this ZDB using redis client

        each of these VM's is automatically connected to the TF Public Zerotier network (TODO: which one is it)

        VM is only connected to the 1 or 2 zerotier networks ! and NAT connection to internet.
        """

        # TODO:*1
        # are there other params?
        pass

    def webgateways_get(self, jwttoken, country="", farmer_name=""):
        """

        ```out
        farmer_id = (S)
        farmer_name = (S)
        name = (s)
        location = ""
        ipaddr_public_4 = ""
        ipaddr_public_6 = ""
        ```

        :return:
        """
        gws = self.wgw_model.get_all()
        if country:
            gws = list(filter(lambda x: x.location.country == country, gws))
        if farmer_name:
            farmers = self.farmers_get()
            farmer_id = [farmer.id for farmer in farmers if farmer.name == farmer_name]
            gws = list(filter(lambda x: x.farmer_id == farmer_id, gws))    
        return gws

    def webgateway_http_proxy_set(self,jwttoken, webgateway_id, virtualhost,backend_ipaddr, backend_port, suffix=""):
        """

        will answer on http & https
        will configure the forward in the selected webgateway

        :param webgateway_id: id of the obj you get through self.webgateways_get()
        :param virtualhost: e.g. docsify.js.org
        :param backend_ipaddr: e.g. 10.10.100.10
        :param backend_port: e.g. 8080
        :param suffix: e.f. /mysub/name/
        :return: ???
        """
        pass

    def webgateway_http_proxy_delete(self,jwttoken ,webgateway_id,virtualhost):
        """
        delete all info for the specified virtualhost
        :param webgateway_id:
        :param virtualhost:
        :return:
        """
        pass

    def farmer_register(self, jwttoken, farmername, emailaddr="",mobile="",pubkey=""):
        """

        :param farmername: official farmer name as in tf-dir
        :param emailaddr: comma separated list of email addr
        :param mobile: comma separated list of mobile tel nr's (can be used for sms, ...)
        :param pubkey: pubkey of farmer
        :param description
        :return:
        """
        pass

    def webgateway_register(self, jwttoken, etcd_url, etcd_secret, farmername,
                                    pubip4="", pubip6="", country="", name="", location=""):
        """
        allows a farmer to register
        :param jwttoken is token as used in IYO
        :param etcd_url its the url which allows this bot to configure the required forwards
        :param etcd_secret is the secret for the etcd connection
        :param farmername:
        :param pubip4: comma separated list of public ip addr, ip v4
        :param pubip6: comma separated list of public ip addr, ip v6
        :param name: chosen name for the webgateway
        :param country: country as used in self.countries_get...
        :param location: chosen location name
        :param description
        :return:
        """
        pass
