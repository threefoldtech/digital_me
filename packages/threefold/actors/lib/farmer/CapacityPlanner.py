from Jumpscale import j

JSBASE = j.application.JSBaseClass
VM_TEMPLATE = 'github.com/threefoldtech/0-templates/vm/0.0.1'


class CapacityPlanner(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)
        self.models = None

    def zos_reserve(self,node, vm_name, memory=1024, cores=1, zerotier_net="", adminsecret=""):
        """

        deploys a zero-os for a customer

        :param node: is the node from model to deploy on
        :param vm_name: name freely chosen by customer
        :param memory: Amount of memory in MiB (defaults to 1024)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param zerotier_net: is optional additional network to connect to
        :param adminsecret: is the secret which is set on the redis for the ZOS of the customer

        :return: (node_robot_url, servicesecret, ipaddr_zos,redisport)

        user can now connect the ZOS client to this ipaddress with specified adminsecret over SSL

        each of these ZOS'es is automatically connected to the TF Public Zerotier network (TODO: which one is it)

        ZOS is only connected to the 1 or 2 zerotier networks ! and NAT connection to internet.

        """
        #TODO: *1

    def ubuntu_reserve(self,node, vm_name, memory=2048, cores=2, zerotier_net="", pubsshkey=""):
        """

        deploys a ubuntu 18.04 for a customer on a chosen node

        :param node: is the node from model to deploy on
        :param vm_name: name freely chosen by customer
        :param memory: Amount of memory in MiB (defaults to 1024)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param zerotier_net: is optional additional network to connect to
        :param pubsshkey: is the pub key for SSH authorization of the VM

        :return: (node_robot_url, servicesecret,ipaddr_vm)

        user can now connect to this ubuntu over SSH, port 22 (always), only on the 2 zerotiers

        each of these VM's is automatically connected to the TF Public Zerotier network (TODO: which one is it)

        VM is only connected to the 1 or 2 zerotier networks ! and NAT connection to internet.

        """
        #TODO: *1

    #LETS MAKE HIDDEN method which is used by the ones above
    def _vm_reserve(self, node, vm_name, memory=128, cores=1, nics=None, ports=None, configs=None, zt_identity=None,
                   flist='https://hub.grid.tf/tf-bootable/ubuntu:latest.flist', tags=None, ):
        """
        reserve on zos node (node model obj) a vm

        example flists:
        - https://hub.grid.tf/tf-bootable/ubuntu:latest.flist

        :param node: node model obj (see models/node.toml)
        :param vm_name: the name of vm service to be able to use the service afterwards
        :param memory: Amount of memory in MiB (defaults to 128)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param nics: list of nics to attach to the vm defaults to [{'type': 'default', 'name': 'defaultnic'}]
        :param ports: list of open ports on the vm i.e. [{'source': 22, 'target': 22, 'name': 'ssh'}]
        :param configs: list of config i.e. [{'path': '/root/.ssh/authorized_keys',
                                              'content': 'ssh-rsa AAAAB3NzaC1yc2..',
                                              'name': 'sshkey'}]
        :param zt_identity: VM zerotier ID
        :param flist: flist to boot the vm from (defaults to ubuntu flist)
        :param tags: list of tags
        :return:
        """
        # the node robot should send email to the 3bot email address with the right info (access info)
        # for now we store the secret into the reservation table so also this farmer robot can do everything
        # in future this will not be the case !

        # TODO Enable attaching disks

        ipxe_url = ""

        if not nics:
            nics = [{'type': 'default', 'name': 'defaultnic'}]
        if not ports:
            ports = []
        if not configs:
            configs = []
        if not tags:
            tags = []
        j.clients.zrobot.get(instance=node.node_zos_id, data={"url": node.noderobot_ipaddr})
        robot = j.clients.zrobot.robots[node.node_zos_id]
        data = {
            'name': vm_name,
            'memory': memory,
            'cpu': cores,
            'nics': nics,
            'flist': flist,
            'ports': ports,
            'configs': configs,
            'tags': tags,
            'ztIdentity': zt_identity,
            'ipxeUrl': ipxe_url,
            'disks': [],
            'mounts': [],
        }
        vm_service = robot.services.create(VM_TEMPLATE, vm_name, data)
        vm_service.schedule_action('install').wait(die=True)
        reservation = self.models.reservations.new()
        reservation.secret = vm_service.data.secret
        return vm_service

    def vm_delete(self, node, vm_name):
        j.clients.zrobot.get(instance=node.node_zos_id, data={"url": node.noderobot_ipaddr})
        robot = j.clients.zrobot.robots[node.node_zos_id]
        vm = robot.services.get(name=vm_name)
        vm.schedule_action("uninstall")
        return

    def zdb_reserve(self, node, name_space, size=100, secret="" ):
        """

        :param node: is the node obj from model
        :param size:  in MB
        :param secret: secret to be given to the namespace
        :param name_space: cannot exist yet
        :return: (node_robot_url, servicesecret, ipaddr, port)

        user can now connect to this ZDB using redis client

        each of these VM's is automatically connected to the TF Public Zerotier network (TODO: which one is it)

        VM is only connected to the 1 or 2 zerotier networks ! and NAT connection to internet.
        """

        pass

        # TODO:*1
        # are there other params?

    def zdb_delete(self, node, name_space):
        pass
        # TODO:*1

        # DO SAME FOR GATEWAY
