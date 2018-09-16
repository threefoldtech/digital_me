
from Jumpscale import j
JSBASE = j.application.JSBaseClass

class OrderbookFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.data.orderbook"
        JSBASE.__init__(self)

