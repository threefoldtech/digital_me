
from jumpscale import j





from peewee import *

db = j.data.bcdb.latest.sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class IndexClass(BaseModel):
    id = IntegerField()
    



MODEL_CLASS=j.data.bcdb.MODEL_CLASS
class Model(MODEL_CLASS):

    def __init__(self, bcdb):
        
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="jumpscale.bcdb.test.house")
        
        self.url = "jumpscale.bcdb.test.house"

        
        self.index = IndexClass()
        self.index.create_table()
        

    
    def index_set(self,obj):
        idict={}
        
        idict["id"] = obj.id
        self.index.create(**idict)
    