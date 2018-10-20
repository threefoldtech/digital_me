from Jumpscale import j
import msgpack
# import struct
# import gevent
# from gevent.event import Event
from .BCDBDecorator import *
JSBASE = j.application.JSBaseClass

# is the base class for the model which gets generated from the template
from JumpscaleLib.clients.zdb.ZDBClientBase import ZDBClientBase





class BCDBModel(JSBASE):
    def __init__(self, bcdb, url, zdbclient, index_enable=True):
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
        self.url = url

        self.is_config = False  # when used for config management

        if not isinstance(zdbclient, ZDBClientBase):
            raise RuntimeError("zdbclient needs to be type: JumpscaleLib.clients.zdb.ZDBClientBase")

        self.zdbclient = zdbclient
        self.zdbclient.meta

        self.index_enable = index_enable
        self.autosave = False  # if set it will make sure data is automatically set from object

        self.objects_in_queue = {}

        self.key = "%s_%s"%(zdbclient.nsname,self.url)  #is unique id for a bcdbmodel (unique per zdbclient !)

        self.logger_enable()

    @queue_method
    def index_delete(self):
        self.index.delete().execute()

    @queue_method
    def index_ready(self):
        """
        doesn't do much, just makes sure that we wait that queue has been processed upto this point
        :return:
        """
        return True

    @queue_method
    def index_load(self):
        self.index_delete()
        j.shell()  # TODO:*1
        pass

    @queue_method
    def reset_data(self, zdbclient_admin,die=True,force=False):
        """
        delete the index and all the items from the model


        :raises RuntimeError: raised when the database type is not implemented/supported yet
        :return: return the number of item deleted
        :rtype: int
        """
        self.logger.debug("reset data for model:%s"%self.url)
        self.index_delete(noqueue=True)

        if not force:
            # need to check this database namespace is not used in other models.
            for key, bcdbmodel in self.bcdb.models.items():
                if bcdbmodel.key == self.key:
                    # myself, go out
                    continue
                if bcdbmodel.zdbclient.nsname == self.zdbclient.nsname:
                    msg = "CANNOT DELETE THE NAMESPACE BECAUSE USED BY OTHER BCDBMODELS"
                    if die:
                        raise RuntimeError(msg)
                    else:
                        print(msg)
                        return
        # now I am sure I can remove it
        data = self.zdbclient.meta._data
        zdbclient_admin.namespace_delete(self.zdbclient.nsname)
        zdbclient_admin.namespace_new(self.zdbclient.nsname)
        #lets renew it
        self.zdbclient = j.clients.zdb.client_get(nsname=self.zdbclient.nsname,
                                                  addr=self.zdbclient.addr,
                                                  port=self.zdbclient.port,
                                                  secret=self.zdbclient.secret,
                                                  mode="seq")

        self.zdbclient.meta._data=data
        self.zdbclient.meta.save()

        assert self.zdbclient.get(1) == None


    @queue_method
    def delete(self, obj_id):
        if hasattr(obj_id, "_JSOBJ"):
            obj_id = obj_id.id
        self.zdbclient.delete(obj_id)

    def check(self, obj):
        if not hasattr(obj, "_JSOBJ"):
            raise RuntimeError("argument needs to be a bcdb obj")

    @queue_method
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

    @queue_method_results
    def set(self, obj, index=True):
        """
        :param obj
        :return: obj
        """
        self.check(obj)

        # prepare
        obj = self.set_pre(obj)

        bdata = obj._data

        # later:
        acl = b""
        crc = b""
        signature = b""

        l = [acl, crc, signature, bdata]
        data = msgpack.packb(l)

        if obj.id is None:
            # means a new one
            obj.id = self.zdbclient.set(data)
        else:
            try:
                self.zdbclient.set(data, key=obj.id)
            except Exception as e:
                if str(e).find("only update authorized")!=-1:
                    raise RuntimeError("cannot update object:%s\n with id:%s, does not exist"%(obj,obj.id))
                raise e

        if index:
            self.index_set(obj)

        return obj

    def new(self):
        obj = self.schema.new()
        obj.model = self
        return obj

    def set_pre(self, obj):
        return obj

    def index_set(self, obj):
        pass

    @queue_method_results
    def get(self, id, return_as_capnp=False):
        """
        @PARAM id is an int or a key
        @PARAM capnp if true will return data as capnp binary object,
               no hook will be done !
        @RETURN obj    (.index is in obj)
        """

        if id == None:
            raise RuntimeError("id cannot be None")

        # obj_in_queue = self.objects_in_queue.get(id, None)
        # if obj_in_queue is not None:
        #     obj = self.objects_in_queue[id]
        #     if return_as_capnp:
        #         return obj._data
        #     return obj

        data = self.zdbclient.get(id)

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

    def iterate(self, key_start=None, reverse=False, keyonly=False):
        """
        walk over all the namespace and yield each object in the database

        :param key_start: if specified start to walk from that key instead of the first one, defaults to None
        :param key_start: str, optional
        :param reverse: decide how to walk the namespace
                if False, walk from older to newer keys
                if True walk from newer to older keys
                defaults to False
        :param reverse: bool, optional
        :param keyonly: [description], defaults to False
        :param keyonly: bool, optional
        :raises e: [description]
        """
        self.index_ready()
        for key, data in self.zdbclient.iterate(key_start=key_start, reverse=reverse, keyonly=keyonly):
            if key == 0:  # skip first metadata entry
                continue
            obj = self._unserialize(id, data)
            yield obj

    def get_all(self):
        return [obj for obj in self.iterate()]

    def __str__(self):
        out = "model:%s\n" % self.url
        out += j.core.text.prefix("    ", self.schema.text)
        return out

    __repr__ = __str__
