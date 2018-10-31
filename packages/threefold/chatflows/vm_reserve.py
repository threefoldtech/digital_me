from Jumpscale import j


# THIS IS A TEST CHAT FOR RESERVING VM

def chat(bot):
    farmer = j.tools.threefold_farmer
    farmer.zdb = j.clients.zdb.testdb_server_start_client_get()
    node = farmer.models.nodes.new()
    node.node_zos_id = "00241dcea33e"
    node.noderobot_ipaddr = "http://10.102.53.47:6600"

    """
    to call http://localhost:5050/chat/session/vm
    """
    vm_name = bot.string_ask("Choose name for your vm?")
    zt_token = bot.string_ask("Enter your zerotier token")
    zt_network = bot.string_ask("Enter an extra zerotier network to connect to in addition to the public network:")
    vm_type = bot.single_choice("Select operating system:", ["ubuntu", "zero-os"])
    memory = bot.int_ask("Choose size of memory in megabytes")
    cores = bot.int_ask("Enter number of virtual cores")

    msg = """# You have ordered: an {vm_type} virtual machine with specs:
                - {memory} mb RAM
                - {cores} virtual cores
### Click next to start provisioning of the vm (this may take few minutes)"""
    msg = msg.format(vm_type=vm_type, memory=memory, cores=cores)
    if vm_type == "ubuntu":
        ssh_key = bot.text_ask("Enter your public ssh key to be authorized on the vm?")
        bot.md_show(msg)
        robot_url, service_secret, ip_addresses = farmer.capacity_planner.ubuntu_reserve(
            node=node, vm_name=vm_name, pub_ssh_key=ssh_key, zerotier_token=zt_token, zerotier_network=zt_network
        )
        msg = """## You have successfully reserved ubuntu vm,
you can use the following data to connect to it using your ssh key
         - Node Robot URL : {robot_url}
         - Service Secret: {service_secret}
         - VM IPs:
          -- ZT Network ID 1: {network0} ---> IP: {ip_address0}
          -- ZT Network ID 2: {network1} ---> IP: {ip_address1}
        """.format(robot_url=robot_url, service_secret=service_secret,
                   network0=ip_addresses[0]['network_id'], ip_address0=ip_addresses[0]['ip_address'],
                   network1=ip_addresses[1]['network_id'], ip_address1=ip_addresses[1]['ip_address'])
        bot.md_show(msg)
    elif vm_type == "zero-os":
        organization = bot.string_ask("Enter your organization name to be able to access zero-os using JWT")
        bot.md_show(msg)
        robot_url, service_secret, ip_addresses, port = farmer.capacity_planner.zos_reserve(
            node=node, vm_name=vm_name, zerotier_token=zt_token, zerotier_network=zt_network, organization=organization)
        msg = """
        ## You have successfully reserved Zero-OS vm,
        you can use the following data to connect to it using your zos client
         - Node Robot URL : {robot_url}
         - Service Secret: {service_secret}
         - VM IPs:
          -- ZT Network ID 1: {network0} ---> IP: {ip_address0}
          -- ZT Network ID 2: {network1} ---> IP: {ip_address1}
         - Redis Port: {port}
        """.format(robot_url=robot_url, service_secret=service_secret, port=port,
                   network0=ip_addresses[0]['network_id'], ip_address0=ip_addresses[0]['ip_address'],
                   network1=ip_addresses[1]['network_id'], ip_address1=ip_addresses[1]['ip_address'])
        bot.md_show(msg)
