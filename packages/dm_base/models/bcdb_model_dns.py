from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
# Sell Order
@url = digitalme.dnsrecord
type = "" (S)   # A, AAAA, NS, MX, CNAME, TXT, PTR
val = "" (S)


"""
from peewee import *
db = j.data.bcdb.bcdb_instances["base"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_digitalme_dnsrecord(BaseModel):
    id = IntegerField(unique=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="digitalme.dnsrecord")
        self.url = "digitalme.dnsrecord"
        self.index = Index_digitalme_dnsrecord
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    