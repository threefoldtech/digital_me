from Jumpscale import j
#GENERATED CODE, can now change
from peewee import *


class circle_index:

    def _init_index(self):
        pass #to make sure works if no index

        db = self.bcdb.sqlitedb

        class BaseModel(Model):
            class Meta:
                database = db

        class Index_digitalme_circle(BaseModel):
            id = IntegerField(unique=True)

        self.index = Index_digitalme_circle
        self.index.create_table()

    
    def index_set(self,obj):
        idict={}
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    