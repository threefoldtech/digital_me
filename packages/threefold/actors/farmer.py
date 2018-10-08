from Jumpscale import j

JSBASE = j.application.JSBaseClass


class Farmer(JSBASE):
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
        ```in
        country = "" (S)
        farmer_name = "" (S)
        cores_min_nr = 0 (I)
        mem_min_mb = 0 (I)
        ssd_min_gb = 0 (I)
        hd_min_gb = 0 (I)
        nr_max = 10 (I)
        ```

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
            nodes = list(filter(lambda x: country.lower() in x.location.country.lower(), nodes))
        if farmer_name:
            farmers = self.farmers_get()
            farmer_ids = [farmer.id for farmer in farmers if farmer_name.lower() in farmer.name.lower()]
            nodes = list(filter(lambda x: x.farmer_id in farmer_ids, nodes))
        if cores_min_nr:
            nodes = list(filter(lambda x: x.capacity_total.cru >= cores_min_nr, nodes))
        if mem_min_mb:
            nodes = list(filter(lambda x: x.capacity_total.mru >= mem_min_mb, nodes))
        if ssd_min_gb:
            nodes = list(filter(lambda x: x.capacity_total.sru >= ssd_min_gb, nodes))
        if hd_min_gb:
            nodes = list(filter(lambda x: x.capacity_total.hru >= hd_min_gb, nodes))

        nodes = nodes[:nr_max]
        return nodes

    def zos_reserve(self, jwttoken, node_id, vm_name, memory=1024, cores=1, zerotier_network=""):
        """
        ```in
        jwttoken = (S)
        node_id = (I)
        vm_name = (S)
        memory = 1024 (I)
        cores = 1 (I)
        zerotier_network = "" (S)
        adminsecret = "" (S)
        ```

        deploys a zero-os for a customer

        :param jwttoken: jwt for authentication
        :param node_id: is the id of the node on which you want to deploy
        :param vm_name: name freely chosen by customer
        :param memory: Amount of memory in MiB (defaults to 1024)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param zerotier_network: is optional additional network to connect to

        :return: (node_robot_url, servicesecret, ipaddr_zos,redisport)

        user can now connect the ZOS client to this ipaddress with specified adminsecret over SSL

        each of these ZOS'es is automatically connected to the TF Public Zerotier network (TODO: which one is it)

        ZOS is only connected to the 1 or 2 zerotier networks ! and NAT connection to internet.

        """
        node = self.node_model.get(node_id)
        return self.capacity_planner.zos_reserve(node, vm_name, memory=memory, cores=cores,
                                                 zerotier_network=zerotier_network, organization="")

    def ubuntu_reserve(self, jwttoken, node_id, vm_name, memory=2048, cores=2,
                       zerotier_network="", zerotier_token="", pub_ssh_key=""):
        """
        ```in
        jwttoken = (S)
        node_id = (I)
        vm_name = (S)
        memory = 2028 (I)
        cores = 2 (I)
        zerotier_network = "" (S)
        zerotier_token = "" (S)
        pub_ssh_key = "" (S)
        ```

        deploys a ubuntu 18.04 for a customer on a chosen node
        :param jwttoken: jwt for authentication
        :param node_id: is the id of the node on which you want to deploy
        :param vm_name: name freely chosen by customer
        :param memory: Amount of memory in MiB (defaults to 1024)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param zerotier_network: is optional additional network to connect to
        :param zerotier_token: is optional additional network to connect to will need token to authorize
        :param pub_ssh_key: is the pub key for SSH authorization of the VM

        :return: (node_robot_url, servicesecret,ipaddr_vm)

        user can now connect to this ubuntu over SSH, port 22 (always), only on the 2 zerotiers

        each of these VM's is automatically connected to the TF Public Zerotier network (TODO: which one is it)

        VM is only connected to the 1 or 2 zerotier networks ! and NAT connection to internet.

        """
        node = self.node_model.get(node_id)
        return self.capacity_planner.ubuntu_reserve(node, vm_name, memory=memory, cores=cores,
                                                    zerotier_network=zerotier_network,
                                                    zerotier_token=zerotier_token, pub_ssh_key=pub_ssh_key)

    def zdb_reserve(self, jwt, node_id, zdb_name, name_space, disk_type="ssd",
                    disk_size=10, namespace_size=2, secret=""):
        """
        ```in
        jwttoken = (S)
        node_id = (I)
        zdb_name = (S)
        name_space = (S)
        disk_type = "ssd" (S)
        disk_size = 10 (I)
        namespace_size = 2 (I)
        secret = "" (S)
        ```
        
        :param jwt: jwt for authentication
        :param node_id: is the node_id we need to reserve on
        :param zdb_name: is the name for the zdb
        :param name_space: the first namespace name in 0-db
        :param disk_type: disk type of 0-db (ssd or hdd)
        :param disk_size: disk size of the 0-db in GB
        :param namespace_size: the maximum size in GB for the namespace
        :param secret: secret to be given to the namespace
        :return: (node_robot_url, servicesecret, ip_info)

        user can now connect to this ZDB using redis client
        """
        node = self.node_model.get(node_id)
        return self.capacity_planner.zdb_reserve(node, zdb_name, name_space, disk_type,
                                                 disk_size, namespace_size, secret)

    def web_gateways_get(self, jwttoken, country="", farmer_name=""):
        """
        ```in
        jwttoken = (S)
        country = "" (S)
        farmer_name = "" (S)
        ```

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

    def web_gateway_add_host(self, jwttoken, web_gateway_id, domain, backend_ip, backend_port, suffix=""):
        """
        ```in
        jwttoken = (S)
        web_gateway_id = (I)
        domain = (S)
        backend_ip = (S)
        backend_port = (I)
        suffix = "" (S)
        ```
        
        will configure the a virtual_host in the selected web gateway
        :param jwttoken: jwt for authentication
        :param web_gateway_id: id of the obj you get through self.webgateways_get()
        :param domain: e.g. docsify.js.org
        :param backend_ip: e.g. 10.10.100.10
        :param backend_port: e.g. 8080
        :param suffix: e.f. /mysub/name/
        :return: True if successfully added
        """
        web_gateway = self.wgw_model.get(web_gateway_id)
        node = self.node_model.get(web_gateway.node_id)
        return self.capacity_planner.web_gateway_add_host(node, web_gateway_id, domain,
                                                          backend_ip, backend_port, suffix)

    def web_gateway_remove_host(self, jwttoken, web_gateway_id, domain):
        """
        ```in
        jwttoken = (S)
        web_gateway_id = (I)
        domain = (S)
        ```
        delete all info for the specified domain from web_gateway
        :param web_gateway_id: the web gateway that have the domain to be deleted
        :param domain: the domain to be deleted
        :return:
        """
        web_gateway = self.wgw_model.get(web_gateway_id)
        node = self.node_model.get(web_gateway.node_id)
        return self.capacity_planner.web_gateway_delete_host(node, web_gateway, domain)

    def farmer_register(self, jwttoken, farmername, email_addresses=None, mobile_numbers=None, pubkey=""):
        """
        ```in
        jwttoken = (S)
        farmername = (S)
        email_addresses = [] (LS)
        mobile_numbers = [] (LS)
        pubkey = "" (S)
        ```

        :param farmername: official farmer name as in tf-dir
        :param email_addresses: comma separated list of email addr
        :param mobile_numbers: comma separated list of mobile tel nr's (can be used for sms, ...)
        :param pubkey: pubkey of farmer
        :param description
        :return:
        """
        new_farmer = self.farmer_model.new()
        new_farmer.name = farmername
        new_farmer.emailaddr = email_addresses
        new_farmer.mobile = mobile_numbers
        new_farmer.pubkeys = pubkey
        self.farmer_model.set(new_farmer)
        return

    def web_gateway_register(self, jwttoken, etcd_url, etcd_secret, farmer_id, name="",
                             pubip4=None, pubip6=None, country="", location="", description=""):
        """
        ```in
        jwttoken = (S)
        etcd_url = (S)
        etcd_secret = (S)
        farmer_id = (I)
        name = "" (S)
        country = "" (S)
        location = "" (S)
        description = "" (S)
        pubip4 = [] (LS)
        pubip6 = [] (LS)
        ```

        allows a farmer to register
        :param jwttoken is token as used in IYO
        :param etcd_url its the url which allows this bot to configure the required forwards
        :param etcd_secret is the secret for the etcd connection
        :param farmer_id: the owner farmer of this gateway
        :param pubip4: comma separated list of public ip addr, ip v4
        :param pubip6: comma separated list of public ip addr, ip v6
        :param name: chosen name for the webgateway
        :param country: country as used in self.countries_get...
        :param location: chosen location name
        :param description: web gateway extra description
        :return:
        """
        new_gateway = self.wgw_model.new()
        new_gateway.name = name
        new_gateway.etcd_url = etcd_url
        new_gateway.etcd_secret = etcd_secret
        new_gateway.country = country
        new_gateway.location = location
        new_gateway.farmer_id = farmer_id
        new_gateway.pubip4 = pubip4
        new_gateway.pubip6 = pubip6
        new_gateway.description = description
        self.wgw_model.set(new_gateway)
        return
