from importlib import import_module
from Jumpscale import j
import sys
from peewee import *
JSBASE = j.application.JSBaseClass
from .BCDBIndexModel import BCDBIndexModel
from .RedisServer import RedisServer
from .BCDBDecorator import *
from gevent import queue
from JumpscaleLib.clients.zdb.ZDBClientBase import ZDBClientBase
import msgpack



import gevent

class BCDB(JSBASE):

    def __init__(self, name=None, zdbclient=None):
        JSBASE.__init__(self)

        if name is None or zdbclient is None:
            raise RuntimeError("name and zdbclient needs to be specified")

        if not isinstance(zdbclient, ZDBClientBase):
            raise RuntimeError("zdbclient needs to be type: JumpscaleLib.clients.zdb.ZDBClientBase")

        self.name = name

        if not j.data.types.string.check(self.name):
            raise RuntimeError("name needs to be string")

        self.zdbclient = zdbclient
        self.meta = self.zdbclient.meta  # make sure record 0 has been set

        self.models = {}

        self._sqlitedb = None
        self._data_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb")

        self._models_classes_cache = {}

        self.logger_enable()

        self.zdbclient.meta._models_load(self)

        #needed for async processing
        self.results={}
        self.results_id = 0

        j.data.bcdb.latest = self


        from .ACL import ACL
        from .USER import USER
        from .GROUP import GROUP


        self.acl = self.model_add(ACL(self))
        self.user = self.model_add(USER(self))
        self.group = self.model_add(GROUP(self))

        self.dataprocessor_greenlet = None
        self.dataprocessor_start()

        self._load()

        self.logger.info("BCDB INIT DONE:%s"%self.name)

    def redis_server_start(self,port=6380,secret="123456"):

        self.redis_server = RedisServer(bcdb=self,port=port,secret=secret)
        self.redis_server.init()
        self.redis_server.start()

    def _data_process(self):
        # needs gevent loop to process incoming data

        while True:
            method, args, kwargs, event, returnid = self.queue.get()
            res = method(*args,**kwargs)
            if returnid:
                self.results[returnid]=res
            event.set()

    def dataprocessor_start(self):
        """
        will start a gevent loop and process the data in a greenlet

        this allows us to make sure there will be no race conditions when gevent used or when subprocess
        main issue is the way how we populate the sqlite db (if there is any)

        :return:
        """
        if self.dataprocessor_greenlet is None:
            self.sqlitedb
            self.queue = gevent.queue.Queue()
            self.dataprocessor_greenlet = gevent.spawn(self._data_process)
            self.dataprocessor_state = "RUNNING"


    @queue_method
    def reset(self):
        self.stop()
        j.shell()

    def index_rebuild(self):
        self.logger.warning("index and DB out of sync, need to rebuild all")
        if self._sqlitedb is not None:
            self.sqlitedb.close()
        j.sal.fs.remove(j.sal.fs.joinPaths(self._data_dir, self.name + ".db"))
        self._sqlitedb = None

        self.cache_flush()

        for obj in self.iterate():
            obj.model.index_set(obj) #is not scheduled


    def cache_flush(self):
        #put all caches on zero
        for model in self.models.values():
            if model.cache_expiration>0:
                model.obj_cache = {}
            else:
                model.obj_cache = None
            model._init()


    @property
    def sqlitedb(self):
        if self._sqlitedb is None:
            self._indexfile = j.sal.fs.joinPaths(self._data_dir, self.name + ".db")
            self.logger.debug("SQLITEDB created in %s"%self._indexfile)
            j.sal.fs.createDir(self._data_dir)
            try:
                self._sqlitedb = SqliteDatabase(self._indexfile)
            except Exception as e:
                j.shell()
        return self._sqlitedb



    def reset_data(self):
        """
        remove index, walk over all zdb's & remove data
        :param zdbclient_admin:
        :return:
        """
        self.logger.info("reset data")
        self.zdbclient.flush()  #new flush command
        self.index_rebuild() #will make index empty

    def model_get(self, url):
        url = j.core.text.strip_to_ascii_dense(url).replace(".", "_")
        if url in self.models:
            return self.models[url]
        raise RuntimeError("could not find model for url:%s" % url)

    def model_add(self, model):
        """

        :param model: is the model object  : inherits of self.MODEL_CLASS
        :return:
        """
        if isinstance(model, j.data.bcdb.MODEL_CLASS):
            self.models[model.schema.url] = model
        return self.models[model.schema.url]

    def model_get_from_schema(self, schema, reload=False, dest=None, overwrite=True):
        """
        :param schema: is schema object j.data.schema... or text
        :param namespace, std is the url of the schema
        :return:
        """
        if j.data.types.str.check(schema):
            schema = j.data.schema.get(schema)

        elif not isinstance(schema, j.data.schema.SCHEMA_CLASS):
            raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")

        if schema.key not in self.models:
            cl = self.model_class_get_from_schema(schema=schema, reload=reload, dest=dest, overwrite=overwrite)
            model = cl(bcdb=self)
            self.models[schema.key] = model
            self.zdbclient.meta.schema_set(schema)  # should always be the first record !
        return self.models[schema.key]


    def model_class_get_from_schema(self,schema, reload=False, dest=None, overwrite=True):
        """

        :param schema: is schema object j.data.schema... or text
        :return: class of the model
        """

        if j.data.types.str.check(schema):
            schema = j.data.schema.get(schema)

        elif not isinstance(schema, j.data.schema.SCHEMA_CLASS):
            raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")

        if reload or schema.key not in self._models_classes_cache:

            imodel = BCDBIndexModel(schema=schema)  # model with info to generate
            imodel.enable = True
            imodel.include_schema = True
            tpath = "%s/templates/Model.py" % j.data.bcdb._path

            key = j.core.text.strip_to_ascii_dense(schema.url).replace(".", "_")
            if dest == None:
                dest = "%s/model_%s.py" % (j.data.bcdb.code_generation_dir, key)

            if overwrite or not j.sal.fs.exists(dest):
                self.logger.debug("render model:%s" % dest)
                if dest is None:
                    raise RuntimeError("cannot be None")
                j.tools.jinja2.file_render(tpath, write=True, dest=dest, schema=schema,
                                           schema_text=schema.text, bcdb=self, index=imodel)

            model_class = self.model_class_get_from_file(dest)

            self._models_classes_cache[schema.key] = model_class

        return self._models_classes_cache[schema.key]

    def model_class_get_from_file(self, path):
        """
        add model to BCDB
        is path to python file

        :param namespace, std is the url of the schema

        """

        if not j.sal.fs.exists(path):
            raise RuntimeError("model needs to be of type: j.data.bcdb.MODEL_CLASS or path to model.")

        dpath = j.sal.fs.getDirName(path)
        if dpath not in sys.path:
            sys.path.append(dpath)
            j.sal.fs.touch("%s/__init__.py" % dpath)
        # self.logger.info("model all:%s" % classpath)
        modulename = j.sal.fs.getBaseName(path)[:-3]
        if modulename.startswith("_"):
            return
        try:
            self.logger.info("import module:%s" % modulename)
            model_module = import_module(modulename)
            self.logger.debug("ok")
        except Exception as e:
            # j.shell()
            raise RuntimeError("could not import module:%s in classpath:%s" % (modulename, path), e)

        model_class = model_module.BCDBModel2

        return model_class

    def model_get_from_file(self, path):
        """
        add model to BCDB
        is path to python file

        :param namespace, std is the url of the schema

        """
        cl = self.model_class_get_from_file(path)
        if cl is None:
            return
        model = cl(bcdb=self)
        self.models[model.schema.url] = model
        return model

    def models_add(self, path, overwrite=True):
        """
        will walk over directory and each class needs to be a model
        when overwrite used it will overwrite the generated models (careful)
        :param path:
        :return: None
        """

        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.toml", followSymlinks=True)
        for schemapath in tocheck:
            dest = "%s/bcdb_model_%s.py" % (j.sal.fs.getDirName(schemapath), j.sal.fs.getBaseName(schemapath, True))
            schema = j.data.schema.get(schemapath)
            self.model_get_from_schema(schema=schema, reload=False, dest=dest, overwrite=overwrite)

        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.py", followSymlinks=True)
        for classpath in tocheck:
            self.model_get_from_file(classpath)

    def _load(self):
        return self.zdbclient.meta._models_load(self)

    def _unserialize(self, id, data, return_as_capnp=False, model=None):

        res = msgpack.unpackb(data)

        if len(res) == 3:
            schema_id, acl_id, bdata_encrypted = res
            if model:
                if schema_id != model.schema_id:
                    j.shell()
                    raise RuntimeError("this id: %s is not of right type"%(id))
            else:
                model =self.zdbclient.meta.model_get_id(schema_id,bcdb=self)
        else:
            raise RuntimeError("not supported format in table yet")

        bdata = j.data.nacl.default.decryptSymmetric(bdata_encrypted)

        if return_as_capnp:
            return bdata
        else:
            obj = model.schema.get(capnpbin=bdata)
            obj.id = id
            obj.acl_id = acl_id
            obj.model = model
            if model.write_once:
                obj.readonly = True #means we fetched from DB, we need to make sure cannot be changed
            return obj

    def obj_get(self,id):

        data = self.zdbclient.get(id)
        if data is  None:
            return None
        return self._unserialize(id, data)


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
        for key, data in self.zdbclient.iterate(key_start=key_start, reverse=reverse, keyonly=keyonly):
            if key == 0:  # skip first metadata entry
                continue
            obj = self._unserialize(key, data)
            yield obj

    def get_all(self):
        return [obj for obj in self.iterate()]
