
from Jumpscale import j

JSBASE = j.application.JSBaseClass




class BCDBTableMeta(JSBASE):

    def __init__(self,db):
        JSBASE.__init__(self)
        self.db=db
        data = self.db.dbclient.get(0)
        if data is None:
            self._data = {}
            self._data["schemas"]={}
            self._data["config"]={}
        else:
            self._data = j.data.serializers.msgpack.loads(data)

        j.shell()

    def schema_get(self,id):
        cfg = self._data["schemas"].get(id,{})
        if "hash" not in cfg:
            cfg["hash"]=""
        if "url" not in cfg:
            cfg["url"]=""
        if "schema" not in cfg:
            cfg["schema"]=""

    def schema_set(self,schema_url):
        if j.data.types.string.check(schema_url):
            schema = j.data.schema.get(schema_url,die=False)
            if schema is None:
                if "\n" not in schema_url and j.sal.fs.exists(schema_url):
                    schema_text = j.sal.fs.fileGetContents(schema_url)
                else:
                    schema_text = schema_url
                schema = j.data.schema.add(schema_text)
        else:
            if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
                raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")
        #now we have the proper schema



    def config_get(self,name):
        return self._data["config"].get(name,None)

    def config_set(self,name,val):
        return self._data["config"][name]=val

    def config_exists(self,name):
        return self.config_get(name)is not None

