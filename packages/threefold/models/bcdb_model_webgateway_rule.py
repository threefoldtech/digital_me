from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
@url = threefold.grid.webgateway_rule
rule_name = ""
user* = ""
domains = [] (LS)
backends = [] (LS)
webgateway_name = ""

"""
from peewee import *
db = j.data.bcdb.bcdb_instances["default"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_threefold_grid_webgateway_rule(BaseModel):
    id = IntegerField(unique=True)
    user = TextField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefold.grid.webgateway_rule")
        self.url = "threefold.grid.webgateway_rule"
        self.index = Index_threefold_grid_webgateway_rule
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["user"] = obj.user
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    