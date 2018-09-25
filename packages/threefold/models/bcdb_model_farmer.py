from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""

@url = threefold.grid.farmer
name* = ""
description = ""
error = ""
iyo_org* = ""
wallets = (LS)
emailaddr = (LS)
mobile = (LS)
pubkeys = "" (S)


"""
from peewee import *
db = j.data.bcdb.bcdb_instances["threefold"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_threefold_grid_farmer(BaseModel):
    id = IntegerField(unique=True)
    name = TextField(index=True)
    iyo_org = TextField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefold.grid.farmer")
        self.url = "threefold.grid.farmer"
        self.index = Index_threefold_grid_farmer
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["name"] = obj.name
        idict["iyo_org"] = obj.iyo_org
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    