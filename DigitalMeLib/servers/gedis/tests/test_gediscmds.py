import os

import pytest
from DigitalMeLib.servers.gedis.GedisCmds import (GedisCmds,
                                                  method_source_process)


@pytest.mark.parametrize("input,code,comments,schema_in,schema_out,args", [
    ("""def foo(self):
        pass""", "pass\n", "", "", "", ""),
    ("""def foo(self, a, b):
        pass""", "pass\n", "", "", "", ['a', 'b']),
    ("""def foo(self, a, b):
        \"""
        this is a comment
        \"""
        pass""", "pass\n", "this is a comment\n", "", "", ['a', 'b']),
    ("""def foo(self, a, b):
        \"""
        this is a comment
        ```in
        a = (O) !jumpscale.example.wallet
        ```
        ```out
        b = (O) !jumpscale.example.wallet
        ```
        \"""
        pass""", "pass\n", "this is a comment\n", "a = (O) !jumpscale.example.wallet\n", "b = (O) !jumpscale.example.wallet\n", ['a', 'b'])
])
def test_method_source_process(input, code, comments, schema_in, schema_out, args):
    assert (code, comments, schema_in, schema_out, args) == method_source_process(input)


def test_GedisCmds_init():
    path = os.path.join(os.path.dirname(__file__), 'actors/actor.py')
    cmds = GedisCmds(server=FakeServer(), namespace="default", name="test", path=path, capnpbin=None)
    assert cmds.name == 'test'
    assert cmds.namespace == 'default'
    assert cmds.path == path
    actual_commands = ['args_in', 'bar', 'echo', 'foo', 'ping', 'schema_in', 'schema_in_out', 'schema_out']
    assert list(cmds.cmds.keys()) == actual_commands
    for cmd in actual_commands:
        assert cmds.cmd_exists(cmd)


class FakeServer:
    def __init__(self):
        self.classes = {}
