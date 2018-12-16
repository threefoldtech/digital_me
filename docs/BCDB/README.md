# BCDB
BCDB `Block Chain Database` is a Database built with `Block Chain` concepts. 

## Components
### Models 
the model in BCDB is a class using [JumpScale Schema](/docs/schema/README.md) it adds:
- indexing capabilities 
    - to make data queries go faster you can use indexing with BCDB to the fields you will query with,
 this can be achieved easily by just adding `*` beside the field you want to index in the schema 
        ```
        @url = school.student
        name* = (S)
        subjects = (LS)
        address = !schema.address
        ```
        _if you are not familiar with the [JumpScale Schema](/docs/schema/README.md), it's highly recomended to read
        the schema documentation before proceeding to this part_  
        in the previous schema `name` will be indexing, we will demonstrate how to use that to do a query in the usage
        section
- Hooks
    - you can add hooks to be manipulated before set/get

### Namespaces
to organize the models stored in the database, the database is divided into namespaces, the default namespace is called 
`default`

### Backend
in order to get BCDB to work you should provide a Backend client, A `Backend Client` is a `Jumpscale client` 
for a key value store (ZDB, Redis or ETCD) which will be used to save the data

## How to start a BCDB
You can run BCDB with two options:  
- with ZDB as a backend:
   in this case you should have a zdb server running and a client for it  
   example:   
```python
zdb_cl = j.clients.zdb.client_get(addr='localhost', port='9900', mode="seq", secret="XXX", nsname="mynamespace")
# Then you can start your bcdb
bcdb = j.data.bcdb.new("bcbd_name", zdb_cl)
```
- or you can start it with the integrated key value store implemented with sqlite, in this case you don't need to
 provide a zdb client  
 example:
 ```python
bcdb = j.data.bcdb.new("bcbd_name")
```
    
## Usage
```python
# Define the Schema
schema = """
        @url = school.student
        name* = (S)
        subjects = (LS)
        address = (S)
        """
# Get DB client (we will use zdb test server to start and get zdb client)
db_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)

# Get BCDB databse object
db = j.data.bcdb.get(db_cl,namespace="test",reset=True)

# Create a BCDB model with the previous schema
model = db.model_create(schema=schema)

# Create a new object from the model
o = model.new()

# Fill data 
o.name = "foo"
o.subjects.append("math")
o.subjects.append("science")
o.address = "2 bar street"

# Save object to database
saved_object = model.set(o)

# Now you can get Object with ID
loaded_object = model.get(saved_object.id)

# To query using the indexed fields
qres = model.index.select(model.index.name == "foo")

# IMPORTANT NOTE :
# the query result will contain only the id and the indexed fields
# if you want to get the full model you need to get it fom the model using the ID
queried_object = model.get(qres[0].id)
```

## ACL
BCDB provides ACL (Access Control list) out of the box for all models created.
you can use this ACL to define who can access what from your data, tak a look on the following example to learn
 how to use it.
 ```python
# first we will define users and groups to be used in the acl
user1 = bcdb.user.new()
user1.name = "user1"
user1.email = "user1@user.com"
user1.dm_id = "user1@dm"
user1.save()

group1 = bcdb.group.new() 
group1.name = "group1"  
group1.user_members = [user1.id]
group1.save()

# Define a schema
schema = """
    @url = test5.acl
    name = "" 
    an_id = 0
    """
    
# get model from schema    
model = bcdb.model_get_from_schema(schema)

# Create a new object
test1 = model.new()
test1.name = "test"
# add read right to user1
test1.acl.rights_set(userids = [user1.id], rights="r")
# now the user1 has read only access to this record
assert test1.acl.rights_check(userid=user1.id, rights="r")
assert not test1.acl.rights_check(userid=user1.id, rights="w")
# add write right to group1
test1.acl.rights_set(groupids=[group1.id], rights="w")




```