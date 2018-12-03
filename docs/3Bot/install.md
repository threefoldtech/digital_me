### Prepare 0-robot (farmer robot) and 3bot containers

```python
# Select the node you want to install the containers on it
ZOS_NODE_ID = "ac1f6b457b6c"
ZOS_NODE_IP = "172.30.73.214"

# Prepare nics and zt networks you need to attach to each container
NICS = [
    {'name': "nat0", "type": "default"},
    # Extra zerotier networks you need to join
    {"name": "zerotier", "type": "zerotier", "id": "17d709436cba92e7"},
]

# Prepare containers data
CONTAINERS = [
    {
        "name": "ubuntu-digitalme",
        "container_data": {
            'flist': "https://hub.grid.tf/tf-bootable/ubuntu:18.04.flist",
            'mounts': [{'source': '/var/run/redis.sock', 'target': '/tmp/redis.sock'}],
            'nics': NICS,
        }
    },
    {
        "name": "ubuntu-zrobot",
        "container_data": {
            'flist': "https://hub.grid.tf/tf-bootable/ubuntu:16.04.flist",
            'nics': NICS,
        }
    }
]
```

### Create the containers using node robot and authorize your keys into them
```python
j.clients.zrobot.get(ZOS_NODE_ID, data={"url": "http://{}:6600".format(ZOS_NODE_IP)})
robot = j.clients.zrobot.robots.get(ZOS_NODE_ID)
zos = j.clients.zos.get(ZOS_NODE_ID, data={"host": ZOS_NODE_IP})
for con in CONTAINERS:
    print("[-] Creating {} Container".format(con['name']))
    container_service = robot.services.create('container', con['name'], data=con['container_data'])
    container_service.schedule_action('install').wait(die=True)
    print("[+] Created {} Container".format(con['name']))

    print("[-] Starting {} Container".format(con['name']))
    container_service.schedule_action('start').wait(die=True)
    print("[+] Started {} Container".format(con['name']))

    print("[-] Authorizing SSH KEYS")
    con_zos = zos.containers.get(con['name'])
    con_zos.client.bash("mkdir -p /root/.ssh").get()
    ssh_key = j.clients.sshkey.get("id_rsa").pubkey
    con_zos.client.bash("echo '%s' > /root/.ssh/authorized_keys" % ssh_key).get()
    print("[+] Keys authorized")
    con_zos.client.filesystem.chmod("/etc/ssh", 0o700, True)
    con_zos.client.bash("service ssh start").get()
```

### Install 0-robot on ubutnu-zrobot container:
ssh into the container then run the following:
```bash
export JUMPSCALEBRANCH="development"
export JSFULL=1
curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/$JUMPSCALEBRANCH/install.sh?$RANDOM > /tmp/install_jumpscale.sh;bash /tmp/install_jumpscale.sh
apt-get install -y libsqlite3-dev
mkdir -p /opt/code/github/threefoldtech
cd /opt/code/github/threefoldtech
git clone https://github.com/threefoldtech/0-robot.git
cd 0-robot
pip install -e .
```

### Start 0-robot
```bash
zrobot server start -T git@github.com:threefoldtech/0-templates.git#development --debug  --god
```

### Install 3bot on ubuntu-digitalme container:
ssh into the container then run the following:
```bash
export JUMPSCALEBRANCH="development_simple"
export JSFULL=1
curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/$JUMPSCALEBRANCH/install.sh?$RANDOM > /tmp/install_jumpscale.sh;bash /tmp/install_jumpscale.sh
pip3 install prometheus_client
```

### start 3bot
```bash
js_shell "j.servers.digitalme.start()"
```
