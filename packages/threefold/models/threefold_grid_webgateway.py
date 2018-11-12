from Jumpscale import j
#GENERATED CODE CAN CHANGE

SCHEMA="""

@url = threefold.grid.webgateway
name* = ""
description = ""
country = ""
location = ""
etcd_host = ""
etcd_port = ""
etcd_secret = ""
node_id = ""
farmer_id = (I)
pubip4 = [] (LS)
pubip6 = [] (LS)

"""


bcdb = j.data.bcdb.latest
schema = j.data.schema.get(SCHEMA)
Index_CLASS = bcdb._BCDBModelIndexClass_generate(schema,__file__)
MODEL_CLASS = bcdb._BCDBModelClass_get()


class threefold_grid_webgateway(Index_CLASS,MODEL_CLASS):
    def __init__(self):
        MODEL_CLASS.__init__(self, bcdb=bcdb,schema=schema)
        self.write_once = False
        self._init()