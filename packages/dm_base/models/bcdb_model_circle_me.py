from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
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
from peewee import *

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class BCDBModel2(MODEL_CLASS):
    def __init__(self, bcdb):

        MODEL_CLASS.__init__(self, bcdb=bcdb, url="digitalme.circle.me")
        self.url = "digitalme.circle.me"
        self._init()

    def _init(self):
        pass #to make sure works if no index

        db = self.bcdb.sqlitedb

        class BaseModel(Model):
            class Meta:
                database = db

        class Index_digitalme_circle_me(BaseModel):
            id = IntegerField(unique=True)

        self.index = Index_digitalme_circle_me
            
        self.index.create_table()


        self.index = Index_digitalme_circle_me
        self.index.create_table()

    
    def index_set(self,obj):
        idict={}
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    