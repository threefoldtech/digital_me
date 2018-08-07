import socket
import time
import struct
from jumpscale import j
from netifaces import interfaces, ifaddresses


TEMPLATE = """
group = "ff15:7079:7468:6f6e:6465:6d6f:6d63:6173"
port = 8123
"""

JSConfigBase = j.tools.configmanager.base_class_config


class MulticastClient(JSConfigBase):
    def __init__(self, instance, data=None, parent=None, interactive=False):
        if not data:
            data = {}
        JSConfigBase.__init__(self, instance=instance, data=data, parent=parent, template=TEMPLATE,
                              interactive=interactive)

    def send(self):
        # Get zerotier ipv6
        for iface_name in interfaces():
            if "zt" not in iface_name:
                continue
            while True:
                addresses = ifaddresses(iface_name).get(socket.AF_INET6)
                if not addresses:
                    time.sleep(5)
                else:
                    break
            bind_ip = addresses[0]['addr']
            break
        else:
            raise RuntimeError("You are not connected to zerotier")

        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.bind((bind_ip, 0))
        while True:
            data = str(time.time()).encode()
            s.sendto(data, (self.config.data['group'], self.config.data['port']))
            time.sleep(1)

    def listen(self):
        # Create a socket
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        # Bind it to the port
        s.bind(("", self.config.data['port']))

        # Join multicast group
        group_bin = socket.inet_pton(socket.AF_INET6, self.config.data['group'])
        mreq = group_bin + struct.pack('@I', 0)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

        # Loop, printing any data we receive
        while True:
            data, sender_address = s.recvfrom(1500)
            while data[-1:] == '\0':
                data = data[:-1]  # Strip trailing \0's
            print(str(sender_address) + '  ' + repr(data))
