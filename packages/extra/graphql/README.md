### `graphql` Package

Adds support for graphql queries `if enabled`

##### How to Test?

- In config file `dm_package.toml` set `enable` to `true`
- restart digital me : `js_shell 'j.servers.digitalme.start()`
- open browser with URL `127.0.0.1:8000/graphql`
- Test Query

  ![](docs/query.png?raw=true)
- Test Mutation

  ![](docs/mutation.png?raw=true)

##### Automatic Queries created for all models in other loaded packages

- By default, `graphql` package is loaded as the last package, so it can detect all models/schemas
from all other packages and create automatic queries for each model

- Examples

  ![](docs/autoQuery1.png?raw=true)

   ![](docs/autoQuery2.png?raw=true)

##### How to use in production?

- To use graphql through `HTTP` clients, use the end point `127.0.0.1:8000/graphql/api` and `POST` requests

##### How to add graphql support in your app/package

- create a file called `graphql_.py` inside your package which gonna contain queries & mutations for this package
- To create queries or mutations please refer to  [Graphene](https://docs.graphene-python.org/en/latest/) library docs
- Make sure your query classes inherit from `DigitalMeLib.graphql import BaseQuery`
- Make sure your mutation classes inherit from `DigitalMeLib.graphql import BaseMutation`
- **examples**:
    - **Query** defined in a `graphql_.py` file:
        ```python
        import graphene
        from DigitalMeLib.graphql import BaseQuery, BaseMutation


        class Query(BaseQuery):
            hello = graphene.String(argument=graphene.String(default_value="stranger"))

            def resolve_hello(self, info, argument):
                return 'Hello ' + argument
        ```
