from flask import Flask
from flask_graphql import GraphQLView
from graphene_utils.utils import createGrapheneClass

import graphene

app = Flask(__name__)

NestedObject = createGrapheneClass(
    "NestedObject", [("name", str), ("age", int), ("body", "json")])


class DataObject(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.age = kwargs.get('age')
        self.body = kwargs.get('body')


class Query(graphene.ObjectType):
    hello = graphene.String(argument=graphene.String(default_value="stranger"))
    data = graphene.Field(NestedObject)
    class_data = graphene.Field(NestedObject)

    def resolve_hello(self, info, argument):
        return 'Hello ' + argument

    def resolve_data(self, info, **kwargs):
        return {"name": "James", "age": 23, "body": {'data': "Hello worlds"}}

    def resolve_class_data(self, info, **kwargs):
        return DataObject(name="Sholly", age=24, body=["Names", "Class"])


schema = graphene.Schema(query=Query)

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

# Optional, for adding batch query support (used in Apollo-Client)
# app.add_url_rule(
#     '/graphql/batch',
#     view_func=GraphQLView.as_view('graphql', schema=schema, batch=True))

if __name__ == "__main__":
    app.run()
