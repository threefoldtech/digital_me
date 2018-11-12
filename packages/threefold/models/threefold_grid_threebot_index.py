from Jumpscale import j
#GENERATED CODE, can now change
from peewee import *


class threefold_grid_threebot_index:

    def _init_index(self):
        pass #to make sure works if no index

        db = self.bcdb.sqlitedb

        class BaseModel(Model):
            class Meta:
                database = db

        class Index_threefold_grid_threebot(BaseModel):
            id = IntegerField(unique=True)
            email = TextField(index=True)
            reputation = TextField(index=True)

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

    