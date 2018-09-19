from random import randint

from Jumpscale import j

JSBASE = j.application.JSBaseClass
VM_TEMPLATE_UID = 'github.com/threefoldtech/0-templates/dm_vm/0.0.1'
ZT_TEMPLATE_UID = "github.com/threefoldtech/0-templates/zerotier_client/0.0.1"


class CapacityPlanner(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)
        self.models = None

    def vm_reserve(self, node, vm_name, zt_mgmt_id, zt_token, memory=128, cores=1, ports=None, tags=None,
                   configs=None, disks=None):
        """
        reserve on zos node (node model obj) a vm
        :param node: node model obj (see models/node.toml)
        :param vm_name: the name of vm service to be able to use the service afterwards
        :param memory: Amount of memory in MiB (defaults to 128)
        :param cores: Number of virtual CPUs (defaults to 1)
        :param ports: list of open ports on the vm i.e. [{'source': 22, 'target': 22, 'name': 'ssh'}]
        :param configs: list of config i.e. [{'path': '/root/.ssh/authorized_keys',
                                              'content': 'ssh-rsa AAAAB3NzaC1yc2..',
                                              'name': 'sshkey'}]
        :param zt_mgmt_id: VM zerotier ID
        :param zt_token: zerotier token to authorize the vm
        :param tags: list of tags
        :param disks: Disks to be attached to the vm
        :return:
        """
        # the node robot should send email to the 3bot email address with the right info (access info)
        # for now we store the secret into the reservation table so also this farmer robot can do everything
        # in future this will not be the case !

        if not disks:
            disks = [{
                'diskType': 'hdd',
                'size': 10,
                'mountPoint': '/mnt',
                'filesystem': 'btrfs',
                'label': 'test',
            }]
        if not ports:
            ports = []
        if not configs:
            configs = []
        if not tags:
            tags = []
        j.clients.zrobot.get(instance=node.node_id, data={"url": node.noderobot_ipaddr})
        robot = j.clients.zrobot.robots[node.node_id]
        data = {
            'token': zt_token
        }
        zt_service_name = 'main_{}'.format(randint(100, 999))
        robot.services.create(ZT_TEMPLATE_UID, zt_service_name, data=data)
        data = {
            'nodeId': node.node_id,
            'memory': memory,
            'cpu': cores,
            'image': 'ubuntu',
            'ports': ports,
            'configs': configs,
            'tags': tags,
            'disks': disks,
            'mgmtNic': {'id': zt_mgmt_id, 'ztClient': zt_service_name, 'type': 'zerotier'},
            'mounts': []
        }
        vm = robot.services.create(VM_TEMPLATE_UID, vm_name, data)
        vm.schedule_action('install').wait(die=True)
        reservation = self.models.reservations.new()
        reservation.secret = vm.secret
        return vm

    @staticmethod
    def vm_delete(node, vm_name):
        j.clients.zrobot.get(instance=node.node_id, data={"url": node.noderobot_ipaddr})
        robot = j.clients.zrobot.robots[node.node_id]
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
