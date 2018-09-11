from Jumpscale import j
from JumpscaleLib.servers.grid_capacity.server.models import Farmer, Location
# connect to db
zdbclient = j.clients.zdb.testdb_server_start_client_get(start=False)
db = j.data.bcdb.get(zdbclient)
db.tables_get(os.path.join(os.path.dirname(__file__), 'schemas'))

Location = db.tables['location']

counter = 0
for farmer in Farmer.find(id='*'):
    if farmer.location:
        continue

    farmer.location = Location.new()
    Farmer.set(farmer.id, farmer)
    count += 1

print("updated %d documents" % count)
