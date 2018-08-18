#!/usr/bin/sudo python
from importlib import import_module
import sys

from gevent import monkey, signal, event, spawn
monkey.patch_all()

from jumpscale import j

zdb_start = True
name = "test"

def signal_shutdown():
    raise KeyboardInterrupt

def install_zrobot():
    path = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/0-robot")
    j.sal.process.execute("cd %s;pip install -e ."%path)

if "_zrobot" not in j.servers.__dict__.keys():
    #means not installed yet
    install_zrobot()

rack = j.servers.digitalme.server_rack_get()

def configure():
    ws_dir = j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/digital_me/tree/development/digitalme")

    j.servers.gedis.configure(host="localhost", port="8000", ssl=False,
                                       zdb_instance=name, secret="", app_dir=ws_dir, instance=name)
    # configure a local webserver server (the master one)
    j.servers.web.configure(instance=name, port=5050, port_ssl=0, host="localhost", secret="", ws_dir=ws_dir)    

def start_full():
    
    configure()

    j.servers.digitalme.filemonitor_start(gedis_instance_name='test')
    j.servers.digitalme.workers_start(4)

    if zdb_start:
        # starts & resets a zdb in seq mode with name test
        j.clients.zdb.testdb_server_start_client_get(start=True)


    rack.add("gedis", j.servers.gedis.geventservers_get(name))

    # use jumpscale way of doing wsgi server (make sure it exists already)
    ws = j.servers.web.geventserver_get(name)
    rack.add("web", ws)



    go()

def go():

    rack.start()
    tf_dir = j.clients.git.getContentPathFromURLorPath(
        "https://github.com/threefoldfoundation/www_threefold.io/tree/digital-me/blueprints")
    if tf_dir not in sys.path:
        sys.path.insert(0, tf_dir)
    tf_module = import_module('threefoldtoken.routes')
    j.servers.web.latest.app.app.register_blueprint(tf_module.blueprint)

    signal(signal.SIGTERM, signal_shutdown)
    forever = event.Event()
    try:
        forever.wait()
    except KeyboardInterrupt:
        rack.stop()    

def start_wiki():
    
    configure()

    # multicast_client = j.clients.multicast.get(data={"port": 8123}, interactive=False)
    # spawn(multicast_client.send)
    # spawn(multicast_client.listen)

    # for minimal don't need
    # j.servers.digitalme.filemonitor_start(gedis_instance_name='test')

    rack.add("gedis",  j.servers.gedis.geventservers_get(name))
    rack.add("web", j.servers.web.geventserver_get(name))

    go()

# start()

start_wiki()
