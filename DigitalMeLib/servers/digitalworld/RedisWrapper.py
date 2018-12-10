
from Jumpscale import j
# import gevent


class ResidWrapper(j.world.system._JSFactoryBase):

    __jslocation__ = "j.clients.credis_core"

    def __init__(self):

        j.world.system._JSFactoryBase.__init__(self)

        self._client_fallback =  j.clients.redis.core_get()

        from credis import Connection
        self._client =  Connection(path="/sandbox/var/redis.sock")
        self._client.connect()
        assert self._client.execute(b"PING")==b'PONG'

    def execute(self,*args):
        try:
            return self._client.execute(*args)
        except Exception as e:
            raise RuntimeError("Could not execute redis execute:\nargs:%s\nerror:%s"%(args,e))

    def get(self,*args):
        return self.execute("GET",*args)

    def set(self,*args):
        return self.execute("SET",*args)

    def hset(self,*args):
        return self.execute("HSET",*args)

    def hget(self,*args):
        return self.execute("HGET",*args)

    def hdel(self,*args):
        return self.execute("HDEL",*args)

    def keys(self,*args):
        return self.execute("KEYS",*args)

    def delete(self,*args):
        return self.execute("DEL",*args)

    def incr(self,*args):
        return self.execute("INCR",*args)
