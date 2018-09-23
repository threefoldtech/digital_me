from Jumpscale import j

JSBASE = j.application.JSBaseClass
VM_TEMPLATE = 'github.com/threefoldtech/0-templates/vm/0.0.1'


class CapacityPlanner(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)
        self.models = None

    def vm_reserve(self, node, vm_name, memory=128, cores=1, nics=None, ports=None, configs=None, zt_identity=None,
                   flist='https://hub.grid.tf/tf-bootable/ubuntu:latest.flist', tags=None, ipxe_url=""):
        """
        reserve on zos node (node model obj) a vm
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
        :param ipxe_url: ipxe url for zero-os vm
        :return:
        """
        # the node robot should send email to the 3bot email address with the right info (access info)
        # for now we store the secret into the reservation table so also this farmer robot can do everything
        # in future this will not be the case !

        # TODO Enable attaching disks
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

    def zdb_reserve(self, node, name_space, size=100, secret="", ):
        """

        :param node: is the node obj from model
        :param size:  in MB
        :param secret: secret to be given to the namespace
        :param name_space: cannot exist yet
        :return:
        """

        pass

        # TODO:*1
        # are there other params?

    def zdb_delete(self, node, name_space):
        pass
        # TODO:*1

        # DO SAME FOR GATEWAY
