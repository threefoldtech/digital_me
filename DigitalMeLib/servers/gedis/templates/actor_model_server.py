

from Jumpscale import j

JSBASE = j.application.JSBaseClass

SCHEMA="""
{{schema.text}}
"""

class model_{{schema.key}}(JSBASE):
    
    def __init__(self):
        JSBASE.__init__(self)        
        # self.namespace = "{{model.key}}"
        self.url = "{{schema.url}}"
        self.bcdb = j.data.bcdb.bcdb_instances["{{model.bcdb.name}}"]
        self.model = self.bcdb.models["{{schema.url}}"]
        self.schema = self.model.schema

    def set(self,data_in):
        if j.servers.gedis.latest.serializer:
            #e.g. for json
            ddict = j.servers.gedis.latest.return_serializer.loads(data_in)
            obj = self.schema.get(data=ddict)
            data = self.schema.data
        else:
            id,data = j.data.serializers.msgpack.loads(data_in)

        res=self.model.set(data=data, key=id)
        if res.id == None:
            raise RuntimeError("cannot be None")

        if j.servers.gedis.latest.serializer:
            return j.servers.gedis.latest.return_serializer.dumps(res.ddict)
        else:
            return j.data.serializers.msgpack.dumps([res.id,res.data])

    def get(self, id):
        id=int(id.decode())
        obj = self.model.get(id=id)
        print("get")
        if j.servers.gedis.latest.serializer:
            return j.servers.gedis.latest.return_serializer.dumps(obj.ddict)
        else:
            return j.data.serializers.msgpack.dumps([obj.id,obj.data])

    def find(self, total_items_in_page=20, page_number=1, only_fields=[], **args):
        #TODO:*1 what is this, who uses it?
        if isinstance(only_fields, bytes):
            import ast
            only_fields = ast.literal_eval(only_fields.decode())
        return self.model.find(hook=self.hook_get, capnp=True, total_items_in_page=total_items_in_page,
                               page_number=page_number, only_fields=only_fields, {{kwargs}})
        
    def new(self):
        return self.model.new()

