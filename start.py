#!/usr/bin/sudo python
from gevent import monkey, signal, event

monkey.patch_all()

from jumpscale import j

zdb_start = True

name = "test"
rack = j.servers.gworld.server_rack_get()

j.servers.gworld.filemonitor_start(gedis_instance_name='test')
j.servers.gworld.workers_start(10)

def signal_shutdown():
    raise KeyboardInterrupt

def start():
    if zdb_start:
        # starts & resets a zdb in seq mode with name test
        j.clients.zdb.testdb_server_start_client_get(start=True)

    ws_dir = j.clients.git.getContentPathFromURLorPath(
        "https://github.com/threefoldtech/digital_me/tree/development/digitalme")

    j.servers.gedis.configure(host="localhost", port="8000", ssl=False,
                                       zdb_instance=name, secret="", app_dir=ws_dir, instance=gedis_instance)

    redis_server = j.servers.gedis.geventservers_get(name)
    rack.add("gedis", redis_server)

    # configure a local webserver server (the master one)
    j.servers.web.configure(instance=name, port=5050, port_ssl=0, host="localhost", secret="", ws_dir=ws_dir)

    # use jumpscale way of doing wsgi server (make sure it exists already)
    ws = j.servers.web.geventserver_get(name)
    rack.add("web", ws)

    # get zrobot instance
    zrobot = j.servers.zrobot.get(name, data={"template_repo": "git@github.com:threefoldtech/0-templates.git",
                                  "block": False})
    rack.add('zrobot', zrobot)

    rack.start()

    signal(signal.SIGTERM, signal_shutdown)
    forever = event.Event()
    try:
        forever.wait()
    except KeyboardInterrupt:
        rack.stop()    

start()
