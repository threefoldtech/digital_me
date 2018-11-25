from Jumpscale import j


JSBASE = j.application.JSBaseClass


class example(JSBASE):
    """
    """

    # def __init__(self):
    #     JSBASE.__init__(self)


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

        r=schema_out.new()
        r.cat = "acat"
        r.msg = "name was: %s"%name
        r.options = ["acat"]

        return r

    def ping(self):
        return 'PONG' 
