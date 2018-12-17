from Jumpscale import j

JSBASE = j.application.JSBaseClass


class actor(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)

    def ping(self):
        return "pong"

    def foo(self):
        return "foo"

    def bar(self):
        return "bar"

    def echo(self, input):
        return input
