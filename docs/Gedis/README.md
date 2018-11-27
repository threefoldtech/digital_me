# Gedis
Gedis is a [Gevent server](http://www.gevent.org/servers.html) using [Redis Protocol](https://redis.io/topics/protocol)
and [BCDB](/doc/BCDB/README.md) to provide fast and easy to use API

## Actors
Actors are the place where you put your application logic, it's like endpoints in a restful api, it takes a request 
with specific data and returns a response, however you don't directly send data to it, it's the generated client role

## what is the generated client
Gedis uses Redis protocol to send data over the socket connection, so here comes the role of the generated client, 
it provides a simple way to deal with the gedis server without caring about how to serialize your in or out data.

## How to use

- First you need to have an actor that contains one or more action, each action has a `schema_in` which represents the 
request data structure and a `schema_out` which represents the response data structure.   
_if you are not familiar with the [JumpScale Schema](/docs/schema/README.md), it's highly recomended to read
 the schema documentation before proceeding to this part_  
 see an Example Actor [here](packages/extra/examples/actors/gedis_examples.py)
 
- Now you can start gedis server and get the client from it
```python

# Start gedis test server in tmux
cmd = "js_shell 'j.servers.gedis.test_server_start()'"
j.tools.tmux.execute(
    cmd,
    session='main',
    window='gedis_test',
    pane='main',
    session_reset=False,
    window_reset=True
)

#then get a gedis client
client = j.clients.gedis.get("test")

# then you will see that the registered actors are loaded in the client 
# so you can perform actions directly using the client 
client.gedis_examples.echo("s")

```
**to see more usage examples please read the tests in [gedis_factory class](DigitalMeLib/servers/gedis/GedisFactory.py)**


## JavaScript Client
A JavaScript Client similar to the python one is also generated so you can use it in your frontend in the same way
```python
    js_code = j.servers.gedis.latest.code_js_client
```