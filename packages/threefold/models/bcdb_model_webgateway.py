from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
@url = threefold.grid.webgateway
name* = ""
description = ""
country = ""
location = ""
etcd_host = ""
etcd_port = ""
etcd_secret = ""
node_id = ""
farmer_id = (I)
pubip4 = [] (LS)
pubip6 = [] (LS)


"""
from peewee import *
db = j.data.bcdb.bcdb_instances["default"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_(BaseModel):
    id = IntegerField(unique=True)
    name = TextField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb, zdbclient):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefold.grid.webgateway", zdbclient=zdbclient)
        self.url = "threefold.grid.webgateway"
        self.index = Index_
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["name"] = obj.name
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    