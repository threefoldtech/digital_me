
## Intro

bcdb = blockchain database

- model is a class using the jumpscale schema
- it adds 
    - indexing capabilities
    - hooks so data can be manipulated before set/get
- the models are organized in namespace and stored in
    - j.data.bcdb.models[$namespace]
    - the default namespace = "default"


## use of redis for difficult situations (possible deadlocks)

- each BCDB has a namespace name
- it has following queues / hsets
- jumpscale:bcdb:$namespacename:datachanges is the queue which processes all data changes
- jumpscale:bcdb:$namespacename:$modelurl is a hset with the data, they key is the id

format of data = json

