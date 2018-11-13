from Jumpscale import j
#GENERATED CODE, can now change
from peewee import *


class threefold_grid_reservation_index:

    def _init_index(self):
        pass #to make sure works if no index
        self.logger.info("init index:%s"%self.schema.url)

        db = self.bcdb.sqlitedb
        print(db)

        class BaseModel(Model):
            class Meta:
                print("*%s"%db)
                database = db

        class Index_threefold_grid_reservation(BaseModel):
            id = IntegerField(unique=True)
            threebot_id = TextField(index=True)
            date_start = IntegerField(index=True)
            date_end = IntegerField(index=True)
            state = TextField(index=True)
            node_id = IntegerField(index=True)

        self.index = Index_threefold_grid_reservation
        self.index.create_table(safe=True)

    
    def index_set(self,obj):
        idict={}
        idict["threebot_id"] = obj.threebot_id
        idict["date_start"] = obj.date_start
        idict["date_end"] = obj.date_end
        idict["state"] = obj.state
        idict["node_id"] = obj.node_id
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    