from Jumpscale import j
import msgpack
import struct
import gevent
JSBASE = j.application.JSBaseClass

# is the base class for the model which gets generated from the template


class BCDBModel(JSBASE):
    def __init__(self, bcdb, url, namespace=None, index_enable=True):
        """
        for query example see http://docs.peewee-orm.com/en/latest/peewee/query_examples.html

        e.g.
        ```
        query = self.index.name.select().where(index.cost > 0)
        for item in self.select(query):
            print(item.name)
        ```
        """

        JSBASE.__init__(self)

        if bcdb is None:
            raise RuntimeError("bcdb should be set")
        self.bcdb = bcdb
        self.schema = j.data.schema.get(url=url)

        self.is_config = False  # when used for config management

        if namespace:
            self.namespace = namespace
        else:
            self.namespace = j.core.text.strip_to_ascii_dense(self.schema.url).replace(".", "_")

        if self.bcdb.dbclient.type == "ZDB":
            self.db = self.bcdb.dbclient.namespace_new(self.namespace)  # will check if it exists, if not create

        else:
            self.db = self.bcdb.dbclient

        self.db.type = self.bcdb.dbclient.type

        self.db.meta

        self.index_enable = index_enable
        self.autosave = False  # if set it will make sure data is automatically set from object

        self.objects_in_queue = {}

    def index_delete(self):
        self.index.delete().execute()

    def index_load(self):
        self.index_delete()
        j.shell()  # TODO:*1
        pass
        # self.logger.info("build index done")

    def destroy(self,die=True):
        """
        delete the index and all the items from the model


        :raises RuntimeError: raised when the database type is not implemented/supported yet
        :return: return the number of item deleted
        :rtype: int
        """
        delete_nr = 0
        self.index_delete()
        if self.db.type == "RDB":
            for key in self.db.hkeys("bcdb:%s:data" % self.namespace):
                self.db.hdel("bcdb:%s:data" % self.namespace, key)
                delete_nr += 1
            self.db.delete("bcdb:%s:lastid" % self.namespace)
            return delete_nr
        else:
            myns= self.db.nsname #the namespace I want to remove
            #need to check this database namespace is not used in other models.
            for key,bcdbmodel in self.bcdb.models.items():
                if bcdbmodel.namespace == self.namespace:
                    #myself, go out
                    continue
                if bcdbmodel.db.nsname == myns:
                    msg = "CANNOT DELETE THE NAMESPACE BECAUSE USED BY OTHER BCDBMODELS"
                    if die:
                        raise RuntimeError(msg)
                    else:
                        print(msg)
                        return
            #now I am sure I can remove it
            ns=self.db.zdbclient.namespace_get(self.namespace)
            secret = ns.secret
            nsname = ns.nsname

            self.db.zdbclient.namespace_delete(nsname)
            self.db = self.bcdb.dbclient.namespace_new(self.namespace)

            return 1

    def delete(self, obj_id):
        """

        :param obj_id: can be obj or obj id
        :return:
        """

        if hasattr(self, "_JSOBJ"):
            obj_id = self.id

        # make sure the object is no longer remembered for queue processing
        if self.bcdb.gevent_data_processing and obj_id in self.objects_in_queue:
            # will first dump to a queue, so we know its all processed by 1 greenlet and nothing more
            self.objects_in_queue.pop(obj_id)

        if self.db.type == "ZDB":
            self.db.delete(obj_id)
        else:
            self.db.hdel("bcdb:%s:data" % self.namespace, obj_id)

        # TODO:*1 need to delete the part of index !!!

    def check(self, obj):
        if not hasattr(obj, "_JSOBJ"):
            raise RuntimeError("argument needs to be a bcdb obj")

    def set_dynamic(self, data, obj_id=None):
        """
        if string -> will consider to be json
        if binary -> will consider data for capnp
        if obj -> will check of JSOBJ
        if ddict will put inside JSOBJ
        """
        if j.data.types.string.check(data):
            data = j.data.serializers.json.loads(data)
            if obj_id == None and "id" in data:
                obj_id = data["id"]
            obj = self.schema.get(data)
        elif j.data.types.bytes.check(data):
            obj = self.schema.get(capnpbin=data)
            if obj_id is None:
                raise RuntimeError("objid cannot be None")
        elif getattr(data, "_JSOBJ", None):
            obj = data
            if obj_id is None and obj.id is not None:
                obj_id = obj.id
        elif j.data.types.dict.check(data):
            if obj_id == None and "id" in data:
                obj_id = data["id"]
            obj = self.schema.get(data)
        else:
            raise RuntimeError("Cannot find data type, str,bin,obj or ddict is only supported")
        obj.id = obj_id  # do not forget
        return self.set(obj)

    def set(self, obj):
        """
        :param obj
        :return:
        """
        self.check(obj)
        if self.bcdb.gevent_data_processing:
            if obj.id is None:
                # means is first time object, need to ask unique id to db
                obj = self._set(obj=obj, index=False)  # should not do index, will be done later to avoid race condition
            self.objects_in_queue[obj.id] = obj
            # will first dump to a queue, so we know its all processed by 1 greenlet and nothing more
            self.bcdb.queue.put([self.url, obj])
            return obj
        else:
            return self._set(obj=obj)

    def _set(self, obj, index=True):
        """

        @RETURN JSOBJ

        """
        # prepare
        obj = self.set_pre(obj)

        bdata = obj._data

        # later:
        acl = b""
        crc = b""
        signature = b""

        l = [acl, crc, signature, bdata]
        data = msgpack.packb(l)

        if self.db.type == "ZDB":
            if obj.id is None:
                # means a new one
                obj.id = self.db.set(data)
            else:
                self.db.set(data, key=obj.id)
        else:
            if obj.id is None:
                # means a new one
                obj.id = self.db.incr("bcdb:%s:lastid" % self.namespace)-1
            self.db.hset("bcdb:%s:data" % self.namespace, obj.id, data)

        if index:
            self.index_set(obj)

        return obj

    def new(self):
        obj = self.schema.new()
        obj.model = self
        return obj

    def index_ready(self):
        """
        do not forget to call this before doing a search on index
        this will make sure the index is fully populated
        will wait till all objects are processed by indexer (the greenlet which processes the data, only 1 per bcdb)
        :return: True when empty
        """
        if self.bcdb.gevent_data_processing:
            counter = 1
            while len(self.objects_in_queue) > 0:
                gevent.sleep(0.001)
                counter += 1
                if counter == 10000:
                    raise RuntimeError("should never take this long to index, something went wrong")
        return True

    def set_pre(self, obj):
        return obj

    def index_set(self, obj):
        pass

    def get(self, id, return_as_capnp=False):
        """
        @PARAM id is an int or a key
        @PARAM capnp if true will return data as capnp binary object,
               no hook will be done !
        @RETURN obj    (.index is in obj)
        """

        if id == None:
            raise RuntimeError("id cannot be None")

        obj_in_queue = self.objects_in_queue.get(id, None)
        if obj_in_queue is not None:
            obj = self.objects_in_queue[id]
            if return_as_capnp:
                return obj._data
            return obj

        if self.db.type == "ZDB":
            data = self.db.get(id)
        else:
            data = self.db.hget("bcdb:%s:data" % self.namespace, id)

        if not data:
            return None

        return self._unserialize(id, data, return_as_capnp=return_as_capnp)

    def _unserialize(self, id, data, return_as_capnp=False, model=None):

        # if self.json_serialize:
        #     res = j.data.serializers.json.loads(data)
        #     obj = self.schema.get(data=res)
        #     obj.id = id
        #     if return_as_capnp:
        #         return obj._data
        #     return obj
        #
        # else:
        res = msgpack.unpackb(data)

        if len(res) == 4:
            acr, crc, signature, bdata = res
        else:
            raise RuntimeError("not supported format in table yet")

        if return_as_capnp:
            return bdata
        else:
            obj = self.schema.get(capnpbin=bdata)
            obj.id = id
            obj.model = self
            return obj

    def iterate(self, method, key_start=None, direction="forward",
                nrrecords=100000, _keyonly=False,
                result=None):
        """walk over the data and apply method as follows

        call for each item:
            '''
            for each:
                result = method(id,obj,result)
            '''
        result is the result of the previous call to the method

        Arguments:
            method {python method} -- will be called for each item found in the file

        Keyword Arguments:
            key_start is the start key, if not given will be start of database when direction = forward, else end

        """
        def method_zdb(id, data, result0):
            method_ = result0["method"]
            obj = self._unserialize(id, data)
            result0["result"] = method_(id=id, obj=obj, result=result0["result"])
            return result0

        if self.db.type == "ZDB":
            result0 = {}
            result0["result"] = result
            result0["method"] = method

            result0 = self.db.iterate(method=method_zdb, key_start=key_start,
                                      direction=direction, nrrecords=nrrecords,
                                      _keyonly=_keyonly, result=result0)

            return result0["result"]

        else:
            # WE IGNORE Nrrecords
            if not direction == "forward":
                raise RuntimeError("not implemented, only forward iteration supported")
            keys = [int(item.decode()) for item in self.db.hkeys("bcdb:%s:data" % self.namespace)]
            keys.sort()
            if len(keys) == 0:
                return result
            if key_start == None:
                key_start = keys[0]
            for key in keys:
                if key >= key_start:
                    obj = self.get(id=key)
                    result = method(id, obj, result)
            return result

    def get_all(self):
        def do(id, obj, result):
            result.append(obj)
            return result
        return self.iterate(do, result=[])

    def __str__(self):
        out = "model:%s\n" % self.namespace
        out += j.core.text.prefix("    ", self.schema.text)
        return out

    __repr__ = __str__
