from jumpscale import j
from JumpscaleLib.servers.grid_capacity.server.models import Farmer, Location
# connect to db
zdbclient = j.clients.zdb.testdb_server_start_client_get(start=False)
db = j.data.bcdb.get(zdbclient)
db.tables_get(os.path.join(os.path.dirname(__file__), 'schemas'))

Capacity = db.tables['capacity']

count_robot_address = 0
count_os_version = 0

for c in Capacity.find(id='*'):
    modified = False
    if c.robot_address == 'not running 0-OS':
        c.robot_address = 'private'
        count_robot_address += 1
        modified = True

    if c.os_version == 'not running 0-OS':
        c.os_version = 'private'
        count_os_version += 1
        modified = True

    if modified:
        Capacity.set(c.id, c)

print("%s entries updated robot_address" % count_robot_address)
print("%s entries updated os_version" % count_os_version)
