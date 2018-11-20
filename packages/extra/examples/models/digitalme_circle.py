from Jumpscale import j
#GENERATED CODE CAN CHANGE

SCHEMA="""


@url = digitalme.circle
#unique global name
name = "" (S) 
#unique aliases
alias = [""] (LS)
ipaddr = "" (S)
ipaddr6 = "" (S)
pubkey = "" (S)
#only used for the subcircles of my circle
privkey = "" (S)
#used to store initial data for a digital me, its a service we optionally do for each DM who asks us too
#max 1kbyte and needs to be signed by the digital.me source
data = "" (S)
#my own accounting to know who belongs to a circle, I keep id's thats why i need to remember
members = [] (LI) 
secret = "" (S)
otp = "" (S)




"""


bcdb = j.data.bcdb.latest
schema = j.data.schema.get(SCHEMA)
Index_CLASS = bcdb._BCDBModelIndexClass_generate(schema,__file__)
MODEL_CLASS = bcdb._BCDBModelClass_get()


class digitalme_circle(Index_CLASS,MODEL_CLASS):
    def __init__(self):
        MODEL_CLASS.__init__(self, bcdb=bcdb,schema=schema)
        self.write_once = False
        self._init()