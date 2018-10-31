from Jumpscale import j


JSBASE = j.application.JSBaseClass

import time

class BASE(JSBASE):

    def __init__(self, zosclient, name):
        JSBASE.__init__(self)
        self.zosclient = zosclient

        if self._zos_redis.get(self._redis_key) is None:
            #does not exist in redis yet
            self.model = self._schema.new()
            self.model.name = name
            self.model.port = self._get_free_port()
            self.model_save()
        else:
            json = self._zos_redis.get(self._redis_key).decode()
            self.model = self._schema.get(data=j.data.serializers.json.loads(json))

        self.model.name = name


        self.logger_enable()

    @property
    def name(self):
        return self.model.name



    @property
    def _zos_redis(self):
        if self.zosclient.client._Client__redis is None:
            self.zosclient.ping()  # otherwise the redis client does not work
        return self.zosclient.client._Client__redis


    def container_get(self,name="builder",flist=""):
        from .ZOSContainer import ZOSContainer
        zc = ZOSContainer(zos=self, name=name)
        j.shell()


    def model_save(self):
        """
        register the model with the ZOS in the redis db
        :return:
        """
        json = self.model._json
        return self._zos_redis.set(self._redis_key, json)


    def done_check(self,name):
        if name in self.model.progress:
            return True
        return False

    def done_set(self,name):
        if not name in self.model.progress:
            self.model.progress.append("jscore_install")
            self.model_save()

    def done_reset(self):
        self.model.progress = []
        self.model_save()


    def __repr__(self):
        return "zos:%s" % self.name

    __str__ = __repr__
