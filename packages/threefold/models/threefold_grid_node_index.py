from Jumpscale import j
#GENERATED CODE, can now change
from peewee import *


class threefold_grid_node_index:

    def _init_index(self):
        pass #to make sure works if no index
        self.logger.info("init index:%s"%self.schema.url)

        db = self.bcdb.sqlitedb
        print(db)

        class BaseModel(Model):
            class Meta:
                print("*%s"%db)
                database = db

        class Index_threefold_grid_node(BaseModel):
            id = IntegerField(unique=True)
            node_zos_id = TextField(index=True)
            node_zerotier_id = TextField(index=True)
            noderobot = BooleanField(index=True)
            noderobot_up_last = IntegerField(index=True)
            noderobot_ipaddr = TextField(index=True)
            sysadmin = BooleanField(index=True)
            sysadmin_up_ping = BooleanField(index=True)
            sysadmin_up_zos = BooleanField(index=True)
            sysadmin_up_last = IntegerField(index=True)
            sysadmin_ipaddr = TextField(index=True)
            tfdir_found = BooleanField(index=True)
            tfdir_up_last = IntegerField(index=True)
            tfgrid_up_ping = BooleanField(index=True)
            tfgrid_up_last = IntegerField(index=True)
            state = TextField(index=True)
            farmer_id = IntegerField(index=True)
            farmer = BooleanField(index=True)
            update = IntegerField(index=True)

        self.index = Index_threefold_grid_node
        self.index.create_table(safe=True)

    
    def index_set(self,obj):
        idict={}
        idict["node_zos_id"] = obj.node_zos_id
        idict["node_zerotier_id"] = obj.node_zerotier_id
        idict["noderobot"] = obj.noderobot
        idict["noderobot_up_last"] = obj.noderobot_up_last
        idict["noderobot_ipaddr"] = obj.noderobot_ipaddr
        idict["sysadmin"] = obj.sysadmin
        idict["sysadmin_up_ping"] = obj.sysadmin_up_ping
        idict["sysadmin_up_zos"] = obj.sysadmin_up_zos
        idict["sysadmin_up_last"] = obj.sysadmin_up_last
        idict["sysadmin_ipaddr"] = obj.sysadmin_ipaddr
        idict["tfdir_found"] = obj.tfdir_found
        idict["tfdir_up_last"] = obj.tfdir_up_last
        idict["tfgrid_up_ping"] = obj.tfgrid_up_ping
        idict["tfgrid_up_last"] = obj.tfgrid_up_last
        idict["state"] = obj.state
        idict["farmer_id"] = obj.farmer_id
        idict["farmer"] = obj.farmer
        idict["update"] = obj.update
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    