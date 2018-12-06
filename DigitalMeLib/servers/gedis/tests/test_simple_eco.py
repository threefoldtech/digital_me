import os
from multiprocessing import Process

from Jumpscale import j


class TestSimpleEcho:

    def setup(self):
        self.server = j.servers.gedis.configure(
            instance='test', port=8889, host='0.0.0.0', ssl=False, adminsecret='')
        actor_path = os.path.join(os.path.dirname(__file__), 'actors/actor.py')
        self.server.actor_add(actor_path)

        self.proc = Process(target=self.server.start, args=())
        self.proc.start()

    def teardown(self):
        self.proc.terminate()
        self.proc.join()

    def test_ping(self):
        client = self.server.client_get()
        assert b'pong' == client.actor.ping()
        assert b'test' == client.actor.echo('test')
