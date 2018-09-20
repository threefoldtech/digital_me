from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""

@url = threefold.grid.threebot
botid = 0 (I)                     #official id on the blockchain for thos bot
botnames = "" (LS)                #botnames list of bot names's $min5char.$min5char e.g. kristof.ibiza
ipaddr = "" (S)                   #ip address how to reach, can change over time
pubkey = ""                       #public key of this 3bot
description = ""
error = ""
secret = ""                       #optional additional secret for reservation (on top of pub key)
email* = ""                       #for now we use email to escalate to the threebot because they are not on the grid yet

reputation* = ""                  #OK, DENY  (to know which ones we want to work with)



"""
from peewee import *
db = j.data.bcdb.bcdb_instances["threefold.grid"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_threefold_grid_threebot(BaseModel):
    id = IntegerField(unique=True)
    email = TextField(index=True)
    reputation = TextField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefold.grid.threebot")
        self.url = "threefold.grid.threebot"
        self.index = Index_threefold_grid_threebot
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["email"] = obj.email
        idict["reputation"] = obj.reputation
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    