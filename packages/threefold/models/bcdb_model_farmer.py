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
db = j.data.bcdb.bcdb_instances["test"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_(BaseModel):
    id = IntegerField(unique=True)
    name = TextField(index=True)
    iyo_org = TextField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb, zdbclient):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefold.grid.farmer", zdbclient=zdbclient)
        self.url = "threefold.grid.farmer"
        self.index = Index_
        with open('/tmp/log.log', 'a') as f:
            f.write("creating table %s\n" % "threefold.grid.farmer")
            f.write("\tfields:%s\n" % "[indexfield:name:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x7f52ac389588>, indexfield:iyo_org:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x7f52ac389588>]")
            f.write('\ttable: %s\n\n' % 'indexmodel:\s - indexfield:name:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x7f52ac389588>
 - indexfield:iyo_org:TextField:<Jumpscale.data.types.PrimitiveTypes.String object at 0x7f52ac389588>
')

            
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

    