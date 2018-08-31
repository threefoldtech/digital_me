from jumpscale import j
import msgpack
import struct

JSBASE = j.application.jsbase_get_class()


class BCDBModel(JSBASE):
    def __init__(self, bcdb, schema, name=""):
        """
        """

        JSBASE.__init__(self)

        self.bcdb = bcdb

        self.name = name

        if j.data.types.string.check(schema):
            schema = j.data.schema.schema_add(schema)
        elif "_SCHEMA" in schema.__dict__:
            pass
        else:
            raise RuntimeError("input needs to be schema in text or obj format")

        if self.name == "":
            self.name = schema.name
            if not schema.name:
                raise RuntimeError("schema name cannot be empty")

        self.db = self.bcdb.dbclient.namespace_new(name=name,
                                                   maxsize=0, die=False)
        self.index = j.core.db  # only for now, need better solution in future
        self.schema = schema
        self._index_key = "index:%s:%s" % (self.bcdb.dbclient.instance,
                                           self.name)
        self.index_load()

    def index_delete(self):
        for key in self.index.keys(self._index_key + "*"):
            self.index.delete(key)

    def index_load(self):
        self.index_delete()
        self.logger.info("build index for: %s" % self.name)

        def iload(id, data, result):
            if data:
                index, bdata = msgpack.unpackb(data)
                self._index(index, id)

        self.db.iterate(iload)
        self.logger.info("build index done")

    def destroy(self):
        raise RuntimeError("not implemented yet, need to go to db "
                           "and remove namespace")

    def set(self, data, obj_id=None, hook=None):
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
        bdata = obj.data

        # prepare the object for indexing
        index = {}
        for item in self.schema.index_list:
            r = getattr(obj, item)
            if r:
                index[item] = r

        if hook:
            obj, index = hook(obj, index)

        # later:
        acl = b""
        crc = b""
        signature = b""

        l = [index, bdata]
        data = msgpack.packb(l)

        if not obj_id:
            # means a new one
            obj_id = self.db.set(data)
        else:
            self.db.set(data, id=obj_id)

        obj.id = obj_id
        obj.index = index
        self._index(index, obj_id)
        return obj

    def _index(self, index, id):
        for key, item in index.items():
            if j.data.types.bytes.check(key):
                key = key.decode()
            key2 = self._index_key + ":%s" % key
            res = self.index.hget(key2, item)
            if not res:
                res = struct.pack("<I", id)  # binary pack the id
                self.index.hset(key2, item, res)
            else:
                res = self._index_get(res)
                if id not in res:
                    res.append(id)
                    res = msgpack.packb(res)
                    self.index.hset(key2, item, res)

    def _index_get(self, res):
        if len(res) == 4:
            res = [struct.unpack("<I", res)[0]]
        else:
            res = msgpack.unpackb(res)  # is already list
        return res

    def new(self):
        return self.schema.get()

    def get(self, id, capnp=False, hook=None, only_fields=[]):
        """
        @PARAM capnp if true will return data as capnp binary object,
               no hook will be done !
        @RETURN obj    (.index is in obj)
        """

        if id == None:
            raise RuntimeError("id cannot be None")

        data = self.db.get(id)

        if not data:
            return None

        res = msgpack.unpackb(data)

        if len(res) == 2:
            index, bdata = res
        else:
            raise RuntimeError("not supported format in table yet")

        if capnp:
            if not only_fields:
                return bdata
            else:
                obj = self.schema.get(capnpbin=bdata, only_fields=only_fields)
                return obj.data
        else:
            obj = self.schema.get(capnpbin=bdata, only_fields=only_fields)
            obj.id = id
            obj.index = index
            if hook:
                obj = hook(obj)
            return obj

    def find(self, hook=None, capnp=False, total_items_in_page=20, 
                   page_number=1, only_fields=[], **args):

        total_items_in_page = int(total_items_in_page)
        page_number = int(page_number)

        res = []
        # for each item in passed filter args, get result
        for key, val in args.items():

            if not val:
                continue

            indexkey = self._index_key + ":%s" % key
            ids = []
            if val == '*' or val == b'*':
                for item in self.index.hkeys(indexkey):
                    datadb = self.index.hget(indexkey, item)
                    ids.extend(self._index_get(datadb))
            else:
                datadb = self.index.hget(indexkey, val)
                if datadb is not None:
                    ids.extend(self._index_get(datadb))

            res.append(ids)

        res = [set(item) for item in res]
        if len(res) > 1:
            res = set.intersection(*res)
        elif len(res) == 1:
            res = res[0]
        else:
            return res

        final = []

        # pagination
        start = (page_number - 1) * total_items_in_page
        end = total_items_in_page + start - 1
        current = -1

        for id in res:
            current += 1

            if current < start:
                continue

            if current > end:
                break

            obj = self.get(id=id, capnp=capnp, hook=hook,
                           only_fields=only_fields)
            if not obj:
                continue
            if capnp:
                obj = j.data.serializer.msgpack.dumps([id, obj])
            final.append(obj)
        if capnp:
            final = j.data.serializer.msgpack.dumps(final)
        return final

    # def find(self, total_items_in_page=20, page_number=1, only_fields=[], {{find_args}}):
    #     items = self.redis.execute_command("model_%s.find" % self.name, total_items_in_page, page_number, only_fields,
    #                                        {{kwargs}})
    #     items = j.data.serializer.msgpack.loads(items)
    #     result = []
    #
    #     for item in items:
    #         id, data = j.data.serializer.msgpack.loads(item)
    #         obj = self.schema.get(capnpbin=data)
    #         obj.id = id
    #         result.append(obj)
    #     return result
