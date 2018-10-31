from Jumpscale import j
from jose import jwt

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
        self._wgw_rule_model = None
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
    def wgw_rule_model(self):
        if not self._wgw_rule_model:
            self._wgw_rule_model = self._bcdb.model_get('threefold.grid.webgateway_rule')
        return self._wgw_rule_model

    @property
    def wgw_model(self):
        if not self._wgw_model:
            self._wgw_model = self._bcdb.model_get('threefold.grid.webgateway')
        return self._wgw_model

    def farmers_get(self, dummy, schema_out):
        """
        ```in
        dummy = ""
        ```
        ```out
        res = (LO) !threefold.grid.farmer
        ```
        :return: [farmer_obj]
        """
        out = schema_out.new()
        out.res = self.farmer_model.get_all()
        return out

    def country_list(self, dummy, schema_out):
        """
        ```in
        dummy = ""
        ```
        ```out
        res = (LS)
        ```
        :return: list of countries
        """
        nodes = self.node_model.get_all()
        out = schema_out.new()
        out.res = list({n.location.country for n in nodes if n.location.country})
        return out

    def node_find(self, country, farmer_name, cores_min_nr, mem_min_mb, ssd_min_gb, hd_min_gb, nr_max,node_zos_id, schema_out):
        """
        ```in
        country = "" (S)
        farmer_name = "" (S)
        cores_min_nr = 0 (I)
        mem_min_mb = 0 (I)
        ssd_min_gb = 0 (I)
        hd_min_gb = 0 (I)
        nr_max = 10 (I)
        node_zos_id = "" (S)
        ```

        ```out
        res = (LO) !threefold.grid.node
        ```

        the capacity checked against is for free (available) capacity (total-used)

        :param country:
        :param farmer_name:
        :param cores_min_nr:
        :param mem_min_mb:
        :param ssd_min_gb:
        :param hd_min_gb:
        :param nr_max: max nr of records to return
        :param node_zos_id:

        :return: [node_objects]

        """
        total_nodes = self.node_model.get_all()
        selected_farmer = None
        if farmer_name:
            farmers = self.farmer_model.get_all()
            for farmer in farmers:
                if farmer_name.lower() == farmer.name.lower():
                    selected_farmer = farmer
                    break
        nodes = []
        for node in total_nodes:
            if country and country.lower() != node.location.country.lower():
                continue
            if selected_farmer and selected_farmer.id != node.farmer_id:
                continue
            if cores_min_nr and cores_min_nr > (node.capacity_total.cru - node.capacity_used.cru):
                continue
            if mem_min_mb and mem_min_mb > (node.capacity_total.mru - node.capacity_used.mru):
                continue
            if ssd_min_gb and ssd_min_gb > (node.capacity_total.sru - node.capacity_used.sru):
                continue
            if hd_min_gb and hd_min_gb > (node.capacity_total.hru - node.capacity_used.hru):
                continue
            if node_zos_id and node_zos_id != node.node_zos_id:
                continue
            nodes.append(node)
        nodes = nodes[:nr_max]
        out = schema_out.new()
        out.res = nodes
        return out

    def zos_reserve(self, jwttoken, node, vm_name, memory, cores, zerotier_token, organization, schema_out):
        """
        ```in
        jwttoken = (S)
        node = (O) !threefold.grid.node
        vm_name = (S)
        memory = 1024 (I)
        cores = 1 (I)
        zerotier_token = "" (S)
        organization = "" (S)
        ```

        ```out
        robot_url = "" (S)
        service_secret = "" (S)
        ip_address = "" (S)
        redis_port = (I)
        ```

        deploys a zero-os for a customer

        :param jwttoken: jwt for authentication
        :param node: is the node object on which you want to deploy
        :param vm_name: name freely chosen by customer
        :param memory: Amount of memory in MiB (defaults to 1024)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param zerotier_token: is the zerotier token to get the ip address
        user can now connect the ZOS client to this ipaddress with specified adminsecret over SSL
        """
        res = self.capacity_planner.zos_reserve(node, vm_name, memory=memory, cores=cores,
                                                organization=organization, zerotier_token=zerotier_token)
        out = schema_out.new()
        out.robot_url, out.service_secret, out.ip_address, out.redis_port = res
        return out

    def ubuntu_reserve(self, jwttoken, node, vm_name, memory, cores,
                       zerotier_network, zerotier_token, pub_ssh_key, schema_out):
        """
        ```in
        jwttoken = (S)
        node = (O) !threefold.grid.node
        vm_name = (S)
        memory = 2048 (I)
        cores = 2 (I)
        zerotier_network = "" (S)
        zerotier_token = "" (S)
        pub_ssh_key = "" (S)
        ```

        ```out
        node_robot_url = "" (S)
        service_secret = "" (S)
        ip_addr1 = "" (S)
        zt_network1 = "" (S)
        ip_addr2 = "" (S)
        zt_network2 = "" (S)
        ```

        deploys a ubuntu 18.04 for a customer on a chosen node
        :param jwttoken: jwt for authentication
        :param node: is the node obj on which you want to deploy
        :param vm_name: name freely chosen by customer
        :param memory: Amount of memory in MiB (defaults to 1024)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param zerotier_network: is optional additional network to connect to
        :param zerotier_token: is optional additional network to connect to will need token to authorize
        :param pub_ssh_key: is the pub key for SSH authorization of the VM

        user can now connect to this ubuntu over SSH, port 22 (always), only on the 2 zerotiers
        each of these VM's is automatically connected to the TF Public Zerotier network (TODO: which one is it)
        VM is only connected to the 1 or 2 zerotier networks ! and NAT connection to internet.
        """
        res = self.capacity_planner.ubuntu_reserve(node, vm_name, memory=memory, zerotier_network=zerotier_network,
                                                   zerotier_token=zerotier_token, pub_ssh_key=pub_ssh_key, cores=cores)
        out = schema_out.new()
        out.node_robot_url, out.service_secret, connection_info = res
        out.ip_addr1 = connection_info[0]['ip_address'] or ""
        out.zt_network1 = connection_info[0]['network_id'] or ""
        out.ip_addr2 = connection_info[1]['ip_address'] or ""
        out.zt_network2 = connection_info[1]['network_id'] or ""
        return out

    def zdb_reserve(self, jwttoken, node, zdb_name, name_space, disk_type,
                    disk_size, namespace_size, secret, schema_out):
        """
        ```in
        jwttoken = (S)
        node = (O) !threefold.grid.node
        zdb_name = (S)
        name_space = (S)
        disk_type = "ssd" (S)
        disk_size = 10 (I)
        namespace_size = 2 (I)
        secret = "" (S)
        ```

        ```out
        robot_url = "" (S)
        service_secret = "" (S)
        ip_address = "" (S)
        storage_ip = "" (S)
        port = "" (S)
        ```

        :param jwttoken: jwt for authentication
        :param node: is the node obj we need to reserve on
        :param zdb_name: is the name for the zdb
        :param name_space: the first namespace name in 0-db
        :param disk_type: disk type of 0-db (ssd or hdd)
        :param disk_size: disk size of the 0-db in GB
        :param namespace_size: the maximum size in GB for the namespace
        :param secret: secret to be given to the namespace
        :return: (node_robot_url, service_secret, ip_info)

        user can now connect to this ZDB using redis client
        """
        res = self.capacity_planner.zdb_reserve(node, zdb_name, name_space, disk_type,
                                                disk_size, namespace_size, secret)
        out = schema_out.new()
        out.robot_url, out.service_secret, ip_info = res
        out.ip_address = ip_info['ip']
        out.storage_ip = ip_info['storage_ip']
        out.port = ip_info['port']
        return out

    def web_gateways_get(self, jwttoken, country, farmer_name, schema_out):
        """
        ```in
        jwttoken = (S)
        country = "" (S)
        farmer_name = "" (S)
        ```

        ```out
        res = (LO) !threefold.grid.webgateway
        ```

        :return:
        """
        gws = self.wgw_model.get_all()
        if country:
            gws = list(filter(lambda x: x.location.country == country, gws))
        if farmer_name:
            farmers = self.farmer_model.get_all()
            farmer_id = [farmer.id for farmer in farmers if farmer.name == farmer_name]
            gws = list(filter(lambda x: x.farmer_id == farmer_id, gws))
        out = schema_out.new()
        out.res = gws
        return out

    def web_gateway_add_host(self, jwttoken, web_gateway, rule_name, domains, backends):
        """
        ```in
        jwttoken = (S)
        web_gateway = (O) !threefold.grid.webgateway
        rule_name = "" (S)
        domains = [] (LS)
        backends = [] (LS)
        ```
        
        will configure the a virtual_host in the selected web gateway
        :param rule_name: the rule name for this config to be referred to afterwards
        :param jwttoken: jwt for authentication
        :param web_gateway: the web gateway object we need to add host in it
        :param domains: list of domains we need to register e.g. ["threefold.io", "www.threefold.io"]
        :param backends: list of backends that the domains will point to e.g. ['10.10.100.10:80', '10.10.100.11:80']
        """
        user = jwt.get_unverified_claims(jwttoken)['username']
        self.capacity_planner.web_gateway_add_host(web_gateway, rule_name, domains, backends)

        # Check if the rule already exist, so we need to update it or create a new one
        res = self.wgw_rule_model.index.select().where(self.wgw_rule_model.index.user == user).execute()
        rules = [self.wgw_rule_model.get(rule.id) for rule in res]
        for user_rule in rules:
            if user_rule.rule_name == rule_name and user_rule.webgateway_name == web_gateway['name']:
                rule = user_rule
                break
        else:
            rule = self.wgw_rule_model.new()
            rule.rule_name = rule_name
            rule.webgateway_name = web_gateway["name"]
            rule.user = user

        rule.domains = domains
        rule.backends = backends
        self.wgw_rule_model.set(rule)
        return

    def web_gateway_list_hosts(self, jwttoken, schema_out):
        """
        ```in
        jwttoken = ""
        ```
        ```out
        res = (LO) !threefold.grid.webgateway_rule
        ```

        :param jwttoken:
        :param schema_out:
        :return:
        """
        user = jwt.get_unverified_claims(jwttoken)['username']
        res = self.wgw_rule_model.index.select().where(self.wgw_rule_model.index.user == user).execute()
        out = schema_out.new()
        out.res = [self.wgw_rule_model.get(rule.id) for rule in res]
        return out

    def web_gateway_delete_host(self, jwttoken, web_gateway, rule_name):
        """
        ```in
        jwttoken = (S)
        web_gateway = (O) !threefold.grid.webgateway
        rule_name = (S)
        ```
        delete all info for the specified domain from web_gateway
        :param web_gateway: the web gateway that have the domain to be deleted
        :param rule_name: the rule name for the config you need to delete
        :return:
        """
        user = jwt.get_unverified_claims(jwttoken)['username']
        res = self.wgw_rule_model.index.select().where(self.wgw_rule_model.index.user == user).execute()
        rules = [self.wgw_rule_model.get(rule.id) for rule in res]
        for rule in rules:
            if rule.rule_name == rule_name and rule.webgateway_name == web_gateway['name']:
                self.capacity_planner.web_gateway_delete_host(web_gateway, rule_name)
                self.wgw_rule_model.delete(rule.id)
                break

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

    def web_gateway_register(self, jwttoken, etcd_host, etcd_port, etcd_secret, farmer_name, name,
                             pubip4, pubip6, country, location, description, schema_out):
        """
        ```in
        jwttoken = (S)
        etcd_host = (S)
        etcd_port = (S)
        etcd_secret = (S)
        farmer_name = (S)
        name = "" (S)
        country = "" (S)
        location = "" (S)
        description = "" (S)
        pubip4 = [] (LS)
        pubip6 = [] (LS)
        ```
        ```out
        res = (O) !threefold.grid.webgateway
        ```

        allows a farmer to register
        :param jwttoken: is token as used in IYO
        :param etcd_host: the etcd host which allows this bot to configure the required forwards
        :param etcd_port: the etcd server port
        :param etcd_secret is the secret for the etcd connection
        :param farmer_name: the owner farmer of this gateway
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
        new_gateway.etcd_host = etcd_host
        new_gateway.etcd_port = etcd_port
        new_gateway.etcd_secret = etcd_secret
        new_gateway.country = country
        new_gateway.location = location
        for farmer in self.farmer_model.get_all():
            if farmer.name == farmer_name:
                new_gateway.farmer_id = farmer.id
        new_gateway.pubip4 = pubip4
        new_gateway.pubip6 = pubip6
        new_gateway.description = description
        new_gateway = self.wgw_model.set(new_gateway)
        out = schema_out.new()
        out.res = new_gateway
        return out
