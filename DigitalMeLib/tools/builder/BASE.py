from Jumpscale import j


JSBASE = j.application.JSBaseClass

import time

class BASE(JSBASE):

    def __init__(self, redis, name, schema):
        JSBASE.__init__(self)
        self._redis = redis
        self._schema = j.data.schema.get(schema)
        if self._redis.get(self._redis_key) is None:
            #does not exist in redis yet
            self.model = self._schema.new()
            self.model.name = name
            self.model_save()
        else:
            json = self._redis.get(self._redis_key).decode()
            self.model = self._schema.get(data=j.data.serializers.json.loads(json))

        self.model.name = name

        self.logger_enable()

    @property
    def name(self):
        return self.model.name

    def model_save(self):
        """
        register the model with the ZOS in the redis db
        :return:
        """
        json = self.model._json
        return self._redis.set(self._redis_key, json)


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
