import os
from multiprocessing import Process

import pytest
from Jumpscale import j

from .actors.actor import SCHEMA_IN, SCHEMA_OUT


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

    def test_schema_in(self):
        client = self.server.client_get()
        x = j.data.schema.get(url='gedis.test.in').new()
        x.foo = 'test'
        assert b'test' == client.actor.schema_in(x)

    def test_schema_out(self):
        client = self.server.client_get()
        result = client.actor.schema_out()
        assert result.bar == 'test'

    def test_schema_in_out(self):
        client = self.server.client_get()
        x = j.data.schema.get(url='gedis.test.in').new()
        x.foo = 'test'
        result = client.actor.schema_in_out(x)
        assert result.bar == x.foo

    def test_args_in(self):
        client = self.server.client_get()

        with pytest.raises((ValueError, TypeError)):
            client.actor.args_in(12, 'hello')

        with pytest.raises((ValueError, TypeError)):
            client.actor.args_in({'foo'}, 'hello')

        assert b'hello 1' == client.actor.args_in('hello', 1)
