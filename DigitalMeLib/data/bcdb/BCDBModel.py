from jumpscale import j
import msgpack
import struct

JSBASE = j.application.jsbase_get_class()


class BCDBModel(JSBASE):
    def __init__(self,bcdb=None,schema=None,url=None,index_enable=True):
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
            # bcdb = j.data.bcdb.latest
            raise RuntimeError("bcdb should be set")
        self.bcdb = bcdb
        if url is not None:
            self.schema = j.data.schema.schema_get(url=url)
        else:
            if schema is None:
                schema = SCHEMA #needs to be in code file
            self.schema = j.data.schema.schema_add(schema)
        self.key = j.data.text.strip_to_ascii_dense(self.schema.url).replace(".","_")
        if bcdb.dbclient.type == "RDB":
            self.db = bcdb.dbclient
        else:
            self.db = self.bcdb.dbclient.namespace_new(name=self.key,
                                                       maxsize=0, die=False)
        self.index_enable = index_enable

    def index_delete(self):
        pass

    def index_load(self):
        pass
        # self.logger.info("build index done")

    def destroy(self):
        if bcdb.dbclient.type == "RDB":
            j.shell()
        else:
            raise RuntimeError("not implemented yet, need to go to db "
                                "and remove namespace")

    def set(self, data, obj_id=None):
        """
        if string -> will consider to be json
        if binary -> will consider data for capnp
        if obj -> will check of JSOBJ
        if ddict will put inside JSOBJ

        @RETURN JSOBJ
        
        """
        if j.data.types.string.check(data):
            data = j.data.serializer.json.loads(data)
            obj = self.schema.get(data)
        elif j.data.types.bytes.check(data):
            obj = self.schema.get(capnpbin=data)
        elif getattr(data, "_JSOBJ", None):
            obj = data
            if obj_id is None and obj.id is not None:
                obj_id = obj.id
        elif j.data.types.dict.check(data):
            obj = self.schema.get(data)
        else:
            raise RuntimeError("Cannot find data type, str,bin,obj or "
                                "ddict is only supported")


        bdata = obj._data

        # prepare
        obj = self.set_pre(obj)

        # later:
        acl = b""
        crc = b""
        signature = b""

        l = [acl,crc, signature, bdata]
        data = msgpack.packb(l)

        if self.db.type == "ZDB":
            if obj_id is None:
                # means a new one
                obj_id = self.db.set(data)
            else:
                self.db.set(data, key=obj_id)
        else:
            if obj_id is None:
                # means a new one
                obj_id = self.db.incr("bcdb:%s:lastid" % self.key)-1
            self.db.hset("bcdb:%s"%self.key, obj_id, data)

        obj.id = obj_id

        self.index_set(obj)

        return obj

    def new(self):
        return self.schema.get()

    def set_pre(self,obj):
        return obj

    def index_set(self,obj):
        pass

    def get(self, id, capnp=False):
        """
        @PARAM id is an int or a key
        @PARAM capnp if true will return data as capnp binary object,
               no hook will be done !
        @RETURN obj    (.index is in obj)
        """

        if id == None:
            raise RuntimeError("id cannot be None")

        if self.db.type == "ZDB":
            data = self.db.get(id)
        else:
            data = self.db.hget("bcdb:%s" % self.key, id)

        if not data:
            return None

        return self._get(id,data,capnp=capnp)

    def _get(self, id, data,capnp=False):

        res = msgpack.unpackb(data)

        if len(res) == 4:
            acr, crc, signature, bdata = res
        else:
            raise RuntimeError("not supported format in table yet")

        if capnp:
            # obj = self.schema.get(capnpbin=bdata)
            # return obj.data
            return bdata
        else:
            obj = self.schema.get(capnpbin=bdata)
            obj.id = id
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
            method {python method} -- will be called for each item found
            in the file

        Keyword Arguments:
            key_start is the start key, if not given will be start of 
            database when direction = forward, else end

        """
        def method_zdb(id,data,result0):
            method_ = result0["method"]
            obj = self._get(id,data)
            result0["result"] = method_(id=id,obj=obj,result=result0["result"])
            return result0

        if self.db.type == "ZDB":
            result0 = {}
            result0["result"] = result
            result0["method"] = method

            result0 = self.db.iterate(method=method_zdb,key_start=key_start,
                            direction=direction,nrrecords=nrrecords,
                            _keyonly=_keyonly,result=result0)

            return result0["result"]

        else:
            #WE IGNORE Nrrecords
            if not direction=="forward":
                raise RuntimeError("not implemented, only forward iteration "
                                   "supported")
            keys = [int(item.decode()) for item in \
                    self.db.hkeys("bcdb:%s" % self.key)]
            keys.sort()
            if len(keys)==0:
                return result
            if key_start==None:
                key_start = keys[0]
            for key in keys:
                if key>=key_start:
                    obj = self.get(id=key)
                    result = method(id,obj,result)
            return result




    def __str__(self):
        out = "model:%s\n"%self.key
        out += j.data.text.prefix("    ",self.schema.text)
        return out

    __repr__ = __str__

