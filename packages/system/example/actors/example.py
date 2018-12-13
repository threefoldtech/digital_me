from Jumpscale import j


JSBASE = j.application.JSBaseClass


class example(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self._bcdb = j.servers.digitalme.bcdb

    def test(self, name, schema_out):
        """
        ```in
        name = "" (S)
        ```
        ```out
        cat = "" (S)
        msg = "" (S)
        error = "" (S)
        options = L(S)
        ```
        """

        r = schema_out.new()
        r.cat = "acat"
        r.msg = "name was: %s" % name
        r.options = ["acat"]

        return r

    def ping(self):
        return 'PONG'

    def list_examples(self):
        """
        List objects of type digitalme.exampleobj
        """
        return self._bcdb.model_get("digitalme.exampleobj").get_all()
