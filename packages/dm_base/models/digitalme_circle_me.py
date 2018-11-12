from Jumpscale import j
#GENERATED CODE CAN CHANGE

SCHEMA="""


#who am I, this is my own information
@url = digitalme.circle.me
name = "" (S) 
alias = [""] (LS)
privkey = "" (S)
email = [""] (LS)
#list of admin circles who have unlimited access to this circle
admins = [] (LI)
#who are the members of this circle, this does not give them unlimited rights but can use some services of this circle
members = [] (LI) 
secret = "" (S)
otp = "" (S)
iyouser = "" (S)

"""


bcdb = j.data.bcdb.latest
schema = j.data.schema.get(SCHEMA)
Index_CLASS = bcdb._BCDBModelIndexClass_generate(schema,__file__)
MODEL_CLASS = bcdb._BCDBModelClass_get()


class digitalme_circle_me(Index_CLASS,MODEL_CLASS):
    def __init__(self):
        MODEL_CLASS.__init__(self, bcdb=bcdb,schema=schema)
        self.write_once = False
        self._init()