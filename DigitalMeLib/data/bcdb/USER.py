from Jumpscale import j


SCHEMA="""
@url = jumpscale.bcdb.user
name* = ""
dm_id* = ""
email* = ""  
"""


MODEL_CLASS=j.data.bcdb.latest.model_class_get_from_schema(SCHEMA)

class USER(MODEL_CLASS):
    def __init__(self, bcdb):
        MODEL_CLASS.__init__(self, bcdb=bcdb)


    def find(self,name=None,dm_id=None,email=None):
        if dm_id:
            key=dm_id.lower()
        elif email:
            key=email.lower()
        elif name:
            key=name.lower()

        if key not in self._users:

            if id is None:
                if dm_id:
                    dm_id=dm_id.lower()
                elif email:
                    email=email.lower()
                elif name:
                    name=name.lower()
                j.shell()

            self._users[id]=self.model_user.get(id)
            if self._users[id] == None:
                raise RuntimeError("Could not find user:%s (name:%s dm_id:%s email:%s)"%(id,name,dm_id,email))

        return self._users[key]


