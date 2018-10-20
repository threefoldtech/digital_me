from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
@url = digitalme.circle
#unique global name
name = "" (S) 
#unique aliases
alias = [""] (LS)
ipaddr = "" (S)
ipaddr6 = "" (S)
pubkey = "" (S)
#only used for the subcircles of my circle
privkey = "" (S)
#used to store initial data for a digital me, its a service we optionally do for each DM who asks us too
#max 1kbyte and needs to be signed by the digital.me source
data = "" (S)
#my own accounting to know who belongs to a circle, I keep id's thats why i need to remember
members = [] (LI) 
secret = "" (S)
otp = "" (S)





"""
from peewee import *
db = j.data.bcdb.bcdb_instances["base"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_(BaseModel):
    id = IntegerField(unique=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb, zdbclient):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="digitalme.circle", zdbclient=zdbclient)
        self.url = "digitalme.circle"
        self.index = Index_
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    