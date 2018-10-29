from Jumpscale import j
#GENERATED CODE, can now change

{% if index.include_schema %}
SCHEMA="""
{{schema_text}}
"""
{%- endif %}

{%- if index.enable %}
from peewee import *
{%- endif %}

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class BCDBModel2(MODEL_CLASS):
    def __init__(self, bcdb):

        MODEL_CLASS.__init__(self, bcdb=bcdb, url="{{schema.url}}")
        self.url = "{{schema.url}}"
        self._init()

    def _init(self):
        pass #to make sure works if no index
        {%- if index.enable %}
<<<<<<< HEAD

        db = self.bcdb.sqlitedb

        class BaseModel(Model):
            class Meta:
                database = db
=======
        self.index = Index_{{schema.key}}
            
        self.index.create_table()
>>>>>>> 51f222e977cee2e015c43dab8c71c43f5c844777

        class Index_{{schema.key}}(BaseModel):
            id = IntegerField(unique=True)
            {%- for field in index.fields %}
            {{field.name}} = {{field.type}}(index=True)
            {%- endfor %}
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
