from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
@url = threefold.grid.reservation
threebot_id* = ""         #the user who bought the capacity
payment_secret = ""       #when time is there for renewal the farmer robot will ask the 3bot for payment, needs this secret
description = ""
error = ""

mru_nr = 0 (F)            #nr of units reserved
cru_nr = 0 (F)
sru_nr = 0 (F)
hru_nr = 0 (F)
mru_price = 0 (N)         #price in chosen currency for this unit when reservation started, is price per period
cru_price = 0 (N)
sru_price = 0 (N)
hru_price = 0 (N)

date_start* = 0 (D)       #date when the reservation started
date_end* = 0 (D)         #calculated out of nr of periods, or can be a fixed time
period = 0 (I)            #duration of period in nr of hours, 1 means 1 hour, 24 means 1 day, ...
period_nr = 0 (I)         #nr of periods this reservation has been agreed for

state* = ""                #ACTIVE, SUSPENDED, ERROR, INIT  (init is for start)

node_id* = 0 (I)          #node on which the reservation has been done
node_service_id = "" (S)  #id in which the farmer can ask for deletion of the service, no access only deletion

payments = (LO) !threefold.grid.payment



"""
from peewee import *
db = j.data.bcdb.bcdb_instances["test"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_(BaseModel):
    id = IntegerField(unique=True)
    threebot_id = TextField(index=True)
    date_start = IntegerField(index=True)
    date_end = IntegerField(index=True)
    state = TextField(index=True)
    node_id = IntegerField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb, zdbclient):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefold.grid.reservation", zdbclient=zdbclient)
        self.url = "threefold.grid.reservation"
        self.index = Index_
        with open('/tmp/log.log', 'a') as f:
            f.write("creating table %s\n" % "threefold.grid.reservation")
            f.write("\tfields:%s\n" % "[indexfield:threebot_id:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x105b7f908>, indexfield:date_start:IntegerField:<Jumpscale.data.types.CustomTypes.Date object at 0x1173e0588>, indexfield:date_end:IntegerField:<Jumpscale.data.types.CustomTypes.Date object at 0x1173e05f8>, indexfield:state:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x105b7f908>, indexfield:node_id:IntegerField:<Jumpscale.data.types.PrimitiveTypes.Integer object at 0x1173e0860>]")
            f.write('\ttable: %s\n\n' % 'indexmodel:\s - indexfield:threebot_id:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x105b7f908>
 - indexfield:date_start:IntegerField:<Jumpscale.data.types.CustomTypes.Date object at 0x1173e0588>
 - indexfield:date_end:IntegerField:<Jumpscale.data.types.CustomTypes.Date object at 0x1173e05f8>
 - indexfield:state:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x105b7f908>
 - indexfield:node_id:IntegerField:<Jumpscale.data.types.PrimitiveTypes.Integer object at 0x1173e0860>
')

            
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["threebot_id"] = obj.threebot_id
        idict["date_start"] = obj.date_start
        idict["date_end"] = obj.date_end
        idict["state"] = obj.state
        idict["node_id"] = obj.node_id
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    