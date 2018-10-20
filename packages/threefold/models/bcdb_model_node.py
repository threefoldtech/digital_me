from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
@url = threefold.grid.node

node_zos_id* = ""               #zero os id of the host
node_zerotier_id* = ""          #zerotier id
node_public_ip = ""             #node public ip address

description = ""

macaddresses = [] (LS)          #list of macaddresses found of this node

noderobot* = (B)                #could access the node robot (did answer)
noderobot_up_last* = (D)        #last time that the noderobot was up (last check)
noderobot_ipaddr* = ""          #ipaddress where to contact the noderobot

sysadmin* = (B)                 #is accessible over sysadmin network for support?
sysadmin_up_ping* = (B)         #ping worked over sysadmin zerotier
sysadmin_up_zos* = (B)          #zeroos was reachable (over redis for support = sysadmin
sysadmin_up_last* = (D)         #last time that this node was up on sysadmin network
sysadmin_ipaddr* = ""           #ipaddress on sysadmin network

tfdir_found* = (B)              #have found the reservation in the threefold dir
tfdir_up_last* = (D)            #date of last time the node was updated in the threefold dir

tfgrid_up_ping* = (B)           #ping worked on zerotier public network for the TF Grid
tfgrid_up_last* = 0 (D)         #last date that we saw this node to be up (accessible over ping on pub zerotier net)

state* = ""                     #OK, ERROR, INIT

error = ""                      #there is an error on this node

farmer_id* = (I)
farmer* = false (B)
update* = (D)

capacity_reserved = (O) !threefold.grid.capacity.reserved
capacity_used = (O) !threefold.grid.capacity.used
capacity_total = (O) !threefold.grid.capacity.total
location = (O) !threefold.grid.capacity.location



"""
from peewee import *
db = j.data.bcdb.bcdb_instances["test"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_(BaseModel):
    id = IntegerField(unique=True)
    node_zos_id = TextField(index=True)
    node_zerotier_id = TextField(index=True)
    noderobot = BooleanField(index=True)
    noderobot_up_last = IntegerField(index=True)
    noderobot_ipaddr = TextField(index=True)
    sysadmin = BooleanField(index=True)
    sysadmin_up_ping = BooleanField(index=True)
    sysadmin_up_zos = BooleanField(index=True)
    sysadmin_up_last = IntegerField(index=True)
    sysadmin_ipaddr = TextField(index=True)
    tfdir_found = BooleanField(index=True)
    tfdir_up_last = IntegerField(index=True)
    tfgrid_up_ping = BooleanField(index=True)
    tfgrid_up_last = IntegerField(index=True)
    state = TextField(index=True)
    farmer_id = IntegerField(index=True)
    farmer = BooleanField(index=True)
    update = IntegerField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb, zdbclient):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefold.grid.node", zdbclient=zdbclient)
        self.url = "threefold.grid.node"
        self.index = Index_
        with open('/tmp/log.log', 'a') as f:
            f.write("creating table %s\n" % "threefold.grid.node")
            f.write("\tfields:%s\n" % "[indexfield:node_zos_id:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x7f987cdf2710>, indexfield:node_zerotier_id:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x7f987cdf2710>, indexfield:noderobot:BooleanField:<Jumpscale.data.types.PrimitiveTypes.Boolean object at 0x7f987a5b6b00>, indexfield:noderobot_up_last:IntegerField:<Jumpscale.data.types.CustomTypes.Date object at 0x7f987a5b65f8>, indexfield:noderobot_ipaddr:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x7f987cdf2710>, indexfield:sysadmin:BooleanField:<Jumpscale.data.types.PrimitiveTypes.Boolean object at 0x7f987a5b64e0>, indexfield:sysadmin_up_ping:BooleanField:<Jumpscale.data.types.PrimitiveTypes.Boolean object at 0x7f987a5b6470>, indexfield:sysadmin_up_zos:BooleanField:<Jumpscale.data.types.PrimitiveTypes.Boolean object at 0x7f987a5b63c8>, indexfield:sysadmin_up_last:IntegerField:<Jumpscale.data.types.CustomTypes.Date object at 0x7f987a5b62e8>, indexfield:sysadmin_ipaddr:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x7f987cdf2710>, indexfield:tfdir_found:BooleanField:<Jumpscale.data.types.PrimitiveTypes.Boolean object at 0x7f987a5b6dd8>, indexfield:tfdir_up_last:IntegerField:<Jumpscale.data.types.CustomTypes.Date object at 0x7f987a5b6208>, indexfield:tfgrid_up_ping:BooleanField:<Jumpscale.data.types.PrimitiveTypes.Boolean object at 0x7f987a5b6160>, indexfield:tfgrid_up_last:IntegerField:<Jumpscale.data.types.CustomTypes.Date object at 0x7f987a5b6240>, indexfield:state:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x7f987cdf2710>, indexfield:farmer_id:IntegerField:<Jumpscale.data.types.PrimitiveTypes.Integer object at 0x7f987a5b6e80>, indexfield:farmer:BooleanField:<Jumpscale.data.types.PrimitiveTypes.Boolean object at 0x7f987a5c0128>, indexfield:update:IntegerField:<Jumpscale.data.types.CustomTypes.Date object at 0x7f987a5c02e8>]")
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["node_zos_id"] = obj.node_zos_id
        idict["node_zerotier_id"] = obj.node_zerotier_id
        idict["noderobot"] = obj.noderobot
        idict["noderobot_up_last"] = obj.noderobot_up_last
        idict["noderobot_ipaddr"] = obj.noderobot_ipaddr
        idict["sysadmin"] = obj.sysadmin
        idict["sysadmin_up_ping"] = obj.sysadmin_up_ping
        idict["sysadmin_up_zos"] = obj.sysadmin_up_zos
        idict["sysadmin_up_last"] = obj.sysadmin_up_last
        idict["sysadmin_ipaddr"] = obj.sysadmin_ipaddr
        idict["tfdir_found"] = obj.tfdir_found
        idict["tfdir_up_last"] = obj.tfdir_up_last
        idict["tfgrid_up_ping"] = obj.tfgrid_up_ping
        idict["tfgrid_up_last"] = obj.tfgrid_up_last
        idict["state"] = obj.state
        idict["farmer_id"] = obj.farmer_id
        idict["farmer"] = obj.farmer
        idict["update"] = obj.update
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    