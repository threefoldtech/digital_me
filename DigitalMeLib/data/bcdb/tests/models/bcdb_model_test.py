
from jumpscale import j





from peewee import *

class IndexClass(j.data.bcdb.PEEWEE_INDEX_CLASS):
    id = IntegerField()
    


MODEL_CLASS=j.data.bcdb.MODEL_CLASS
class Model(MODEL_CLASS):

    def __init__(self, bcdb=None):
        print("jumpscale.bcdb.test.house")
        
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="jumpscale.bcdb.test.house")
        
        self.url = "jumpscale.bcdb.test.house"

        
        self.index = IndexClass
        self.index.create_table()
        

    
    def index_set(self,obj):
        idict={}
        
        idict["id"] = obj.id
        self.index.create(**idict)
    