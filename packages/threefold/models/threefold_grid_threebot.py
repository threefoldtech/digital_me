from Jumpscale import j
#GENERATED CODE CAN CHANGE

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


bcdb = j.data.bcdb.latest
schema = j.data.schema.get(SCHEMA)
Index_CLASS = bcdb._BCDBModelIndexClass_generate(schema,__file__)
MODEL_CLASS = bcdb._BCDBModelClass_get()


class threefold_grid_threebot(Index_CLASS,MODEL_CLASS):
    def __init__(self):
        MODEL_CLASS.__init__(self, bcdb=bcdb,schema=schema)
        self.write_once = False
        self._init()