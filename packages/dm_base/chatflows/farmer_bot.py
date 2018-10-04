from Jumpscale import j
from json import loads
from ast import literal_eval


def chat(bot):
    """
    a chatbot to reserve zos vm
    :param bot:
    :return:
    """
    gedis_client = j.servers.gedis.latest.client_get()

    def country_list():
        countries = gedis_client.farmer.country_list()
        report = ""
        countries = literal_eval(countries.decode())
        for country in countries:
            report += "- %s\n" % country
        bot.md_show(report)

    def farmer_register():
        bot.md_show("# NOT IMPLEMENTED YET")

    def farmers_get():
        farmers = gedis_client.farmer.farmers_get()
        report = ""
        farmers = j.data.serializers.json.loads(farmers)
        for farmer in farmers:
            report += "- %s\n" % farmer
        bot.md_show(report)

    def node_find():

        fields = {
            "Country": {"type": "s", "name": "country"},
            "Farmer name": {"type": "f", "name": "farmer_name"},
            "Number of cores": {"type": "i", "name": "cores"},
            "Minimum memory in MB": {"type": "i", "name": "mem_min_mb"},
            "SSD min in GB": {"type": "i", "name": "ssd_min_gb"},
            "HD min in GB": {"type": "i", "name": "hd_min_gb"},
            "Limit": {"type": "i", "name": "nr_max"},
        }
        selected = bot.multi_choice("please select fields you want to find with", list(fields.keys()))
        selected = loads(selected)
        if not selected:
            return
        kwargs = {}
        for field in selected:
            if fields[field]["type"] == "i":
                kwargs[fields[field]["name"]] = bot.int_ask("Enter {}".format(field))
            else:
                kwargs[fields[field]["name"]] = bot.string_ask("Enter {}".format(field))

        nodes = gedis_client.farmer.node_find(**kwargs)
        nodes = j.data.serializers.json.loads(nodes.decode())
        report = ""
        for node in nodes:
            report = report + "# Node :{}\n".format(node["id"])
            for key, value in node.items():
                if isinstance(value, dict):
                    report = report + "* {}:\n".format(key)
                    for key1, value1 in value.items():
                        report = report + "    - *{key}*: {value}  \n".format(key=key1, value=value1)
                    report = report + ""
                else:
                    report = report + "- *{key}*: {value}  \n".format(key=key, value=value)
        if not report:
            report = "No matches found"
        bot.md_show(report)


    def ubuntu_reserve():
        farmers = gedis_client.farmer.farmers_get()
        farmers = [farmer["name"] for farmer in j.data.serializers.json.loads(farmers.decode())]
        jwttoken = bot.string_ask("Please enter your JWT")
        node_id = bot.single_choice("select a farm where you will create your vm", farmers)
        vm_name = bot.string_ask("What will you call it?")
        memory = bot.int_ask("choose the memory size")
        cores = bot.int_ask("choose number of cores")
        zerotier_network = bot.string_ask("Enter your zerotier network id")
        if zerotier_network:
            zerotier_token = bot.string_ask("Enter your zerotier token")
        pub_ssh_key = bot.string_ask("Enter your public ssh key")

        robot_url, service_secret, ip_addresses, port = gedis_client.farmer.ubuntu_reserve(jwttoken=jwttoken,
                                                                                           node_id=node_id,
                                                                                           vm_name=vm_name,
                                                                                           memory=memory, cores=cores,
                                                                                           zerotier_network=zerotier_network,
                                                                                           zerotier_token=zerotier_token,
                                                                                           pub_ssh_key=pub_ssh_key)
        report = """## Ubuntu reserved
# you have succesfully registered a zos vm
- *robot url* = {robot_url}
- *service secret* = {service_secret}
- *ip addresses* = {ip_addresses}
- *port* = port""".format(robot_url=robot_url, service_secret=service_secret, ip_addresses=ip_addresses, port=port)
        bot.md_show(report)

    def webgateway_http_proxy_delete():
        bot.md_show("# NOT IMPLEMENTED YET")

    def webgateway_http_proxy_set():
        bot.md_show("# NOT IMPLEMENTED YET")

    def webgateway_register():
        bot.md_show("# NOT IMPLEMENTED YET")

    def zdb_reserve():
        bot.md_show("# NOT IMPLEMENTED YET")

    def zos_reserve():
        jwttoken = bot.string_ask("Please enter your JWT")
        node_id = bot.string_ask("Please enter a node id")
        vm_name = bot.string_ask("Please enter your VM name")
        memory = bot.int_ask("choose the memory size")
        cores = bot.int_ask("choose number of cores")
        zerotier_network = bot.string_ask("Enter your zerotier network")
        admin_secret = bot.string_ask("Enter your admin secret")
        robot_url, service_secret, ip_addresses, port = gedis_client.farmer.zos_reserve(jwttoken, node_id, vm_name,
                                                                                        memory=memory, cores=cores,
                                                                                        zerotier_network=zerotier_network,
                                                                                        adminsecret=admin_secret)
        report = """## ZOS reserved
# you have succesfully registered a zos vm
- *robot url* = {robot_url}
- *service secret* = {service_secret}
- *ip addresses* = {ip_addresses}
- *port* = port""".format(robot_url=robot_url, service_secret=service_secret, ip_addresses=ip_addresses, port=port)
        bot.md_show(report)
        bot.redirect("https://threefold.me")

    def main():
        methods = {
            "List countries": country_list,
            # "Register a farmer": farmer_register,
            "list farmers": farmers_get,
            "Find a node": node_find,
            "Reserve ubuntu vm": ubuntu_reserve,
            # "Delete web gateway": webgateway_http_proxy_delete,
            # "Set web gateway": webgateway_http_proxy_set,
            # "Register web gateway": webgateway_register,
            # "Reserve ZDB vm": zdb_reserve,
            "Reserve ZOS vm": zos_reserve
        }
        choice = bot.single_choice("what do you want to do", [method for method in methods.keys()])
        methods[choice]()

    main()
