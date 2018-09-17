from Jumpscale import j
import sys

JSBASE = j.application.JSBaseClass


class order_book(JSBASE):
    """
    """
    def __init__(self):
        JSBASE.__init__(self)


    def echo(self, msg):
        return msg


    def wallet_set(self,wallet, schema_out):
        """
        ```in
        !jumpscale.example.wallet
        ```

        ```out
        !jumpscale.example.wallet
        ```

        Verifies JWT and registers user wallet!

        :param jwt: JWT from Itsyouonline
        :param wallet_addr: Wallet address
        :param wallet_ipaddr: Wallet Ip address
        :param schema_out: !threefoldtoken.wallet
        :return: Wallet
        :rtype: !threefoldtoken.wallet
        """
        w = schema_out.new()
        w.ipaddr = wallet.ipaddr
        w.addr = wallet.addr
        w.jwt = wallet.jwt
        return w
