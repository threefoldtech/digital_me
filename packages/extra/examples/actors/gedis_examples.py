from Jumpscale import j
import sys

JSBASE = j.application.JSBaseClass


class gedis_examples(JSBASE):
    """
    """
    def __init__(self):
        JSBASE.__init__(self)


    def echo(self, msg):
        return msg

    # this way is not supported anymore, I will leave it here just as a reference
    # def example1(self,wallet, schema_out):
    #     """
    #     ```in
    #     !jumpscale.example.wallet
    #     ```
    #
    #     ```out
    #     !jumpscale.example.wallet
    #     ```
    #     """
    #     w = schema_out.new()
    #     w.ipaddr = wallet.ipaddr
    #     w.addr = wallet.addr
    #     w.jwt = wallet.jwt
    #     return w

    def example2(self,wallet, schema_out):
        """
        ```in
        wallet = (O) !jumpscale.example.wallet
        ```

        ```out
        !jumpscale.example.wallet
        ```

        """
        w = schema_out.new()

        w.ipaddr = wallet['ipaddr']
        w.addr = wallet['addr']
        w.jwt = wallet['jwt']
        return w

    def example3(self,a, b, c, schema_out):
        """
        ```in
        a = (S)
        b = (B)
        c = (I)
        ```

        ```out
        a = (S)
        b = (B)
        c = (I)
        ```
        """
        w = schema_out.new()
        w.a = a
        w.b = b
        w.c = c
        return w

    def example4(self, wallet, schema_out):
        """
        ```in
        wallet = (O) !jumpscale.example.wallet
        ```

        ```out
        result = (O) !jumpscale.example.wallet
        custom = (S)
        ```
        """
        w = schema_out.new()
        w.result.ipaddr = wallet['ipaddr']
        w.result.addr = wallet['addr']
        w.result.jwt = wallet['jwt']
        w.custom = "custom"
        return w