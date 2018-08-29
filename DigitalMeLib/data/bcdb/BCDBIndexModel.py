from jumpscale import j
import os

JSBASE = j.application.jsbase_get_class()


class IndexField():

    def __init__(self,property):
        self.name = property.name
        self.jumpscaletype = property.jumpscaletype
        if self.jumpscaletype.NAME == "string":
            self.type = "TextField"
        elif self.jumpscaletype.NAME in ["integer",'date']:
            self.type = "IntegerField"
        else:
            j.shell()
            raise RuntimeError("did not find required type for peewee:%s"%self)

    def __str__(self):
        out = "indexfield:%s:%s:%s"%(self.name,self.type,self.jumpscaletype)
        return out

    __repr__ = __str__


class BCDBIndexModel(JSBASE):
    def __init__(self,schema):
        """
        """
        JSBASE.__init__(self)
        self.schema=schema
        if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
            raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")

        self.fields = []

        for p in schema.index_properties:
            self.fields.append(IndexField(p))

    def __str__(self):
        out = "indexmodel:\s"
        for item in self.fields:
            out += " - "+str(item) + "\n"
        return out

    __repr__ = __str__

