import graphene
from DigitalMeLib.graphql import BaseQuery, BaseMutation


class Query(BaseQuery):
    hello = graphene.String(argument=graphene.String(default_value="stranger"))

    def resolve_hello(self, info, argument):
        return 'Hello ' + argument

