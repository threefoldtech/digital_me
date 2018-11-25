
bcdb = blockchain database

- model is a class using the jumpscale schema
- it adds 
    - indexing capabilities
    - hooks so data can be manipulated before set/get
- the models are organized in namespace and stored in
    - j.data.bcdb.models[$namespace]
    - the default namespace = "default"

