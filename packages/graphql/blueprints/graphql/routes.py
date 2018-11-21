from blueprints.graphql import *
from Jumpscale import j
from DigitalMeLib.graphql import BaseQuery, BaseMutation
from flask import request, jsonify
login_manager = j.servers.web.latest.loader.login_manager

from flask_graphql import GraphQLView
import graphene


class TestQuery(BaseQuery):
    """
    Test Query.
    Useful to test if graphql is working or not
    """
    test = graphene.String()

    def resolve_test(self, info):
        return 'success'


class TestMutationFiled(graphene.Mutation):
    ok = graphene.Boolean()

    @classmethod
    def mutate(cls, root, context, **kwargs):
        return cls(ok=True)

class TestMutation(BaseMutation):
    """
    Test Mutation .
    Useful to test if graphql is working or not
    """
    test = TestMutationFiled.Field()

def generateQueriesFromSchemas():
    """
    Loop over all loaded schemas, find ones with (indexed) / searchable fields

    Dynamically create Graphql Queries for these
    """
    classes = []

    for url, schema in j.data.schema.schemas.items():
        if schema.index_list:

            class Q(BaseQuery):
                pass

            args = ''
            for i, field in enumerate(schema.index_list):
                args = args + field + ' = graphene.String()'
                if i < len(schema.index_list) -1:
                    args += ','

            def resolver(url):
                def inner(self, info, **kwargs):
                    model = j.data.bcdb.latest.models[url]
                    res = model.index.select()
                    for arg, value in kwargs.items():
                        if value:
                            res = res.where(getattr(model.index, arg) == value)
                    return [model.get(e) for e in res.execute()]
                return inner

            eval("setattr(Q, url.replace('.', '_'),  graphene.String({0},resolver=resolver(url)))".format(args))
            classes.append(Q)

    type('QQ', tuple(classes), {})

generateQueriesFromSchemas()

Query =type('Query', tuple(BaseQuery.__subclasses__()), {})
Mutation = type('Mutation', tuple(BaseMutation.__subclasses__()), {})

schema = graphene.Schema(query=Query, mutation=Mutation)

# Register routes

## GraphiQl UI
blueprint.add_url_rule('/', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

## API end point

@blueprint.route('/api', methods=["POST"])
def api():
    if request.headers.get('Content-Type', '').lower() != 'application/json':
        return jsonify(errors=['Only accepts Content-Type: application/json']), 400

    data = request.json
    query = data.get('query', None)
    if not query:
        return jsonify(errors=['query field is missing']), 400
    if query:
        try:
            execresult = schema.execute(query)
            if execresult.errors:
                # BAD REQUEST ON ERRORS
                return jsonify(errors=[str(e) for e in execresult.errors]), 400
            result = list(execresult.data.items())[0][1]
            if result is None:
                return '', 404
            return jsonify(execresult.data), 200

        except Exception as ex:
            return jsonify(errors=[str(ex)]), 400