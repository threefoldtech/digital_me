# Gedis documentation

Gedis is a RPC framework that provide automatic generation of client side code at runtime.
Which means you only need to define the server interface and the client will automatically receive the code it needs to talk to the server at connection time.

Currently we support client generation for python and javascript.

Gedis can works directly on top a of a tcp connection or over websocket.
The data are binary encoded during transfert using capnp.  
The communication protocol used is [RESP](https://redis.io/topics/protocol)

## Quick start
### Define server interface
```python
TODO: find example code how to create an actor
```

### Client side
```python
TODO: show how to create a client and receive generated code
```