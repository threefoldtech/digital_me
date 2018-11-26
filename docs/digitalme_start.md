
# getting start with Digital Me 
## Installing Jumpscale 
### for more info check [this]("https://github.com/threefoldtech/jumpscale_core/blob/development/README.md") 


## Start Redis server
``` redis-server --daemonize yes ```

## build zdb 
```bash
js_shell "j.servers.zdb.build()"
js_shell "j.clients.zdb.testdb_server_start_client_get() "
```

## start Digital me
```bash
js_shell "j.servers.digitalme.start()"
```

### now you can access 3bot using this url
```localhost:8000```