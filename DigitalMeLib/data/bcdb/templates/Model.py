
from jumpscale import j


{% if include_schema %}
SCHEMA="""
{{schema.text}}
"""
{% endif %}

{% if index.enable %}
from peewee import *

class IndexClass(j.data.bcdb.PEEWEE_INDEX_CLASS):
    id = IntegerField()
    {% for field in index.fields %}
    {{field.name}} = {{field.type}}(index=True)
    {% endfor %}
{% endif %}

MODEL_CLASS=j.data.bcdb.MODEL_CLASS
class Model(MODEL_CLASS):

    def __init__(self, bcdb=None):
        print("{{schema.url}}")
        {% if include_schema %}
        MODEL_CLASS.__init__(self,bcdb=bcdb, schema=SCHEMA)
        {% else %}
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="{{schema.url}}")
        {% endif %}
        self.url = "{{schema.url}}"

        {% if index.enable %}
        self.index = IndexClass
        self.index.create_table()
        {% endif %}

    {% if index.enable %}
    def index_set(self,obj):
        idict={}
        {% for field in index.fields %}
        idict["{{field.name}}"] = obj.{{field.name}}
        {% endfor %}
        idict["id"] = obj.id
        self.index.create(**idict)
    {% endif %}
