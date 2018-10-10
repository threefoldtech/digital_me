from Jumpscale import j

DEFAULT_CORE_NR = 2
DEFAULT_MEM_SIZE = 2048


def chat(bot):
    """
    a chatbot to reserve zos vm
    :param bot:
    :return:
    """
    gedis_client = j.servers.gedis.latest.client_get()
    countries = gedis_client.farmer.country_list().res
    farmers = gedis_client.farmer.farmers_get().res

    def country_list():
        report = ""
        for country in countries:
            report += "- %s\n" % country
        bot.md_show(report)

    def farmer_register():
        jwttoken = bot.string_ask("Please enter your JWT")
        farmer_name = bot.string_ask("Enter farmer name as stated into the directory:")
        email_address = bot.string_ask("Enter farmer email:")
        mobile_number = bot.string_ask("Enter farmer mobile:")
        farmer_pub_key = bot.text_ask("Public key for the farmer:")
        gedis_client.farmer.farmer_register(jwttoken, farmer_name, email_addresses=[email_address],
                                            mobile_numbers=[mobile_number], pubkey=farmer_pub_key)

    def farmers_get():
        report = ""
        for farmer in farmers:
            report += "- %s\n" % farmer.name
        bot.md_show(report)

    def node_find():
        fields = {
            "Country": {"type": "list", "name": "country", "choices": [country for country in countries]},
            "Farmer name": {"type": "list", "name": "farmer_name", "choices": [farmer.name for farmer in farmers]},
            "Number of cores": {"type": "int", "name": "cores_min_nr"},
            "Minimum memory in MB": {"type": "int", "name": "mem_min_mb"},
            "SSD min in GB": {"type": "int", "name": "ssd_min_gb"},
            "HD min in GB": {"type": "int", "name": "hd_min_gb"},
        }
        selected = bot.multi_choice("please select fields you want to find with", list(fields.keys()))
        selected = j.data.serializers.json.loads(selected)
        kwargs = {}
        for field in selected:
            if fields[field]["type"] == "int":
                kwargs[fields[field]["name"]] = bot.int_ask("Enter {}".format(field))
            else:
                kwargs[fields[field]["name"]] = bot.drop_down_choice("Enter {}".format(field), fields[field]["choices"])
        return kwargs

    def ubuntu_reserve(jwt_token, node, vm_name, zerotier_network, zerotier_token, cores, memory):
        pub_ssh_key = bot.string_ask("Enter your public ssh key")
        robot_url, service_secret, ip_addresses = gedis_client.farmer.ubuntu_reserve(jwttoken=jwt_token,
                                                                                     node=node,
                                                                                     vm_name=vm_name,
                                                                                     memory=memory,
                                                                                     cores=cores,
                                                                                     zerotier_network=zerotier_network,
                                                                                     zerotier_token=zerotier_token,
                                                                                     pub_ssh_key=pub_ssh_key)
        report = """## Ubuntu reserved
# you have successfully registered a zos vm
- *robot url* = {robot_url}
- *service secret* = `{service_secret}`
- *ip addresses* = {ip_addresses}
""".format(robot_url=robot_url, service_secret=service_secret, ip_addresses=ip_addresses)
        bot.md_show(report)

    def web_gateway_http_proxy_delete():
        bot.md_show("# NOT IMPLEMENTED YET")

    def web_gateway_http_proxy_set():
        bot.md_show("# NOT IMPLEMENTED YET")

    def web_gateway_register():
        bot.md_show("# NOT IMPLEMENTED YET")

    def zdb_reserve():
        bot.md_show("# NOT IMPLEMENTED YET")

    def zos_reserve():
        node_id = bot.string_ask("Please enter a node id")
        vm_name = bot.string_ask("Please enter your VM name")
        memory = bot.int_ask("choose the memory size")
        cores = bot.int_ask("choose number of cores")
        zerotier_network = bot.string_ask("Enter your zerotier network")
        admin_secret = bot.string_ask("Enter your admin secret")
        robot_url, service_secret, ip_addresses, port = gedis_client.farmer.zos_reserve(
            jwttoken, node_id, vm_name, memory=memory, cores=cores,
            zerotier_network=zerotier_network, adminsecret=admin_secret
        )
        report = """## ZOS reserved
# you have succesfully registered a zos vm
- *robot url* = {robot_url}
- *service secret* = {service_secret}
- *ip addresses* = {ip_addresses}
- *port* = port""".format(robot_url=robot_url, service_secret=service_secret,
                          ip_addresses=ip_addresses, port=port)
        bot.md_show(report)
        bot.redirect("https://threefold.me")

    def reserve_vm():
        jwt_token = bot.string_ask("Please enter your JWT, "
                                   "(click <a target='_blank' href='/client'>here</a> to get one)")
        node_filters = node_find()
        vm_type = bot.single_choice("what do you want to do", ["Ubuntu", "Zero OS", "Zero DB"])
        vm_name = bot.string_ask("What will you call the vm?")
        zerotier_network = bot.string_ask("Enter your zerotier network id:")
        zerotier_token = ""
        if zerotier_network:
            zerotier_token = bot.string_ask("Enter your zerotier token:")
        candidate_nodes = gedis_client.farmer.node_find(**node_filters)
        if not candidate_nodes.res:
            bot.md_show("No available nodes with these criteria")
            return

        node = candidate_nodes.res[0]
        cores = int(node_filters.get('cores_min_nr', DEFAULT_CORE_NR))
        memory = int(node_filters.get('mem_min_mb', DEFAULT_MEM_SIZE))
        if vm_type == "Ubuntu":
            ubuntu_reserve(jwt_token, node, vm_name, zerotier_network, zerotier_token, cores, memory)
        elif vm_type == "Zero OS":
            pass
        elif vm_type == "Zero DB":
            pass

    def main():
        methods = {
            "List countries": country_list,
            "List farmers": farmers_get,
            "Register a farmer": farmer_register,
            # "Find a node": node_find,
            "Reserve vm": reserve_vm,
            "Register Domain": web_gateway_http_proxy_delete,
            "Delete Domain": web_gateway_http_proxy_set,
            "Register web gateway": web_gateway_register,
            # "Reserve ZDB vm": zdb_reserve,
            # "Reserve ZOS vm": zos_reserve
        }
        choice = bot.single_choice("what do you want to do", [method for method in methods.keys()])
        methods[choice]()

    main()
