# Gedis

Gedis is a RPC framework that provide automatic generation of client side code at runtime.
Which means you only need to define the server interface and the client will automatically receive the code it needs to talk to the server at connection time.

Currently we support client generation for python and javascript.

Gedis can works directly on top a of a tcp connection or over websocket.
The data are binary encoded during transfert using capnp.  
The communication protocol used is [RESP](https://redis.io/topics/protocol)

## Quick start

### Define server interface
The RPC interface are define by creating a python class.
All the public methods of the class will be exposed as remote RPC call that clients can call. We name such a class an `actor`.

Creation of an actor at `/tmp/actor.py`:

```python
from Jumpscale import j

JSBASE = j.application.JSBaseClass

class actor(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)

    def ping(self):
        return "pong"
```

Creation of the gedis service and load our actor:

```python
# configure the server
server = j.servers.gedis.configure(instance='test', port=8889, host='0.0.0.0', ssl=False, adminsecret='')
# load a single actor
server.actor_add('/tmp/actor.py', namespace='demo')
# you can also load a directory that contains multiple actor files
# let's imagine you have a directory structure like
# tree test_actor/
# test_actor/
# ├── actor2.py
# ├── actor.py
# you can load all the actors with
server.actors_add('/tmp/test_actor', namespace='demo')

# start the server
server.start()
```

### Get a client
```python
# create a client
# during the connection, the client will receive the generated code for the actor
client = j.clients.gedis.configure(instance='test', host='192.168.10.10', port=8889, namespace='demo', ssl=False)

# use the client
client.actor.ping()
# result will be b'pong'
```