from Jumpscale import j
#GENERATED CODE, can now change

{% if index.include_schema %}
SCHEMA="""
{{schema.text}}
"""
{%- endif %}
{%- if index.enable %}
from peewee import *
db = j.data.bcdb.latest.sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_{{schema.key}}(BaseModel):
    id = IntegerField(unique=True)
    {%- for field in index.fields %}
    {{field.name}} = {{field.type}}(index=True)
    {%- endfor %}
{%- endif %}

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb):
        {%- if include_schema %}
        MODEL_CLASS.__init__(self,bcdb=bcdb,schema=SCHEMA)
        {%- else %}
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="{{schema.url}}")
        {%- endif %}
        self.url = "{{schema.url}}"
        {%- if index.enable %}
        self.index = Index_{{schema.key}}
        self.index.create_table()

        {%- endif %}
    {% if index.enable %}
    def index_set(self,obj):
        idict={}
        {%- for field in index.fields %}
        {%- if field.jumpscaletype.NAME == "numeric" %}
        idict["{{field.name}}"] = obj.{{field.name}}_usd
        {%- else %}
        idict["{{field.name}}"] = obj.{{field.name}}
        {%- endif %}
        {%- endfor %}
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    {% endif %}
