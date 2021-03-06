from jumpscale import j


SCHEMA="""
@url = jumpscale.bcdb.test.house
@name = test_house
name* = "" (S)
active* = "" (B)
cost* = (N)
room = (LO) !jumpscale.bcdb.test.room


"""
from peewee import *
db = j.data.bcdb.latest.sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_jumpscale_bcdb_test_house(BaseModel):
    id = IntegerField(unique=True)
    name = TextField(index=True)
    active = BooleanField(index=True)
    cost = FloatField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="jumpscale.bcdb.test.house")
        self.url = "jumpscale.bcdb.test.house"
        self.index = Index_jumpscale_bcdb_test_house
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["name"] = obj.name
        idict["active"] = obj.active
        idict["cost"] = obj.cost_usd
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    