from importlib import import_module
from Jumpscale import j
import sys
from peewee import *
import os
JSBASE = j.application.JSBaseClass
from redis import StrictRedis
from .BCDBIndexModel import BCDBIndexModel
from .RedisServer import RedisServer
import gevent
from gevent import queue

SCHEMA = """
@url = jumpscale.bcdb.config
cat = ""
key = ""
config = ""
"""


class BCDB(JSBASE):

    def __init__(self, name=None, dbclient=None):
        JSBASE.__init__(self)

        if name is None or dbclient is None:
            raise RuntimeError("name and dbclient needs to be specified")

        self.name = name

        if not j.data.types.string.check(self.name):
            raise RuntimeError("name needs to be string")

        if dbclient:
            if isinstance(dbclient, j.clients.redis._REDIS_CLIENT_CLASS) or isinstance(dbclient, StrictRedis):
                dbclient.type = "RDB"  # means is redis db
            else:
                dbclient.type = "ZDB"
        self.dbclient = dbclient

        self.models = {}

        self.gevent_data_processing = False
        self.greenlet_data_processor = None

        self._sqlitedb = None
        self._data_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb")

        self._models_add_cache = {}

        cl = self.dbclient.namespace_get("default")
        cl.meta  # make sure record 0 has been set

        for nsname in self.dbclient.namespaces_list():
            j.shell()
            nsclient = self.dbclient.namespace_get(nsname)

            try:
                nsclient.meta
            except Exception as e:
                raise RuntimeError("meta record (record0) wrongly structured of :%s" % nsclient.nsinfo)

            # load models
            nsclient.meta.schemas_load()

    def redis_server_start(self):

        self.redis_server = RedisServer(bcdb=self)
        self.redis_server.init()
        self.redis_server.start()


    def gevent_start(self):
        """
        will start a gevent loop and process the data in a greenlet

        this allows us to make sure there will be no race conditions when gevent used or when subprocess
        main issue is the way how we populate the sqlite db (if there is any)

        :return:
        """
        self.gevent_data_processing = True
        self.queue = gevent.queue.Queue()
        self.greenlet_data_processor = gevent.spawn(self._data_process)

    def _data_process(self):
        # needs gevent loop to process incoming data

        while True:
            url, obj = self.queue.get()
            m = self.models[url]
            if obj.id in m.objects_in_queue:
                m._set(obj=obj, index=True)  # now need to index, now only 1 greenlet can do the indexing
                m.objects_in_queue.pop(obj.id)

    @property
    def sqlitedb(self):
        if self._sqlitedb is None:

            self._indexfile = j.sal.fs.joinPaths(self._data_dir, self.name + ".db")
            j.sal.fs.createDir(self._data_dir)
            self.logger.debug("bcdb:indexdb:%s" % self._indexfile)
            try:
                self._sqlitedb = SqliteDatabase(self._indexfile)
            except Exception as e:
                j.shell()
        return self._sqlitedb

    def reset_index(self):
        j.sal.fs.remove(self._data_dir)

    def model_get(self, url):
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

    def model_add_from_schema(self, schema, namespace=None, reload=False, dest=None, overwrite=True):
        """

        :param schema: is schema object j.data.schema...
        :param namespace, std is the url of the schema
        :return:
        """

        if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
            raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")

        if schema.md5 in self._models_add_cache and reload is False:
            return self._models_add_cache[schema.md5]

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

        m = self.model_add_from_file(dest, namespace=namespace)

        self._models_add_cache[schema.md5] = m

        m.db.meta.schema_set(schema)  # should always be the first record !

        return m

    def model_add_from_file(self, path, namespace=None):
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

        model = model_module.Model(bcdb=self, namespace=namespace)

        self.models[model.schema.url] = model

        return model

    def models_add(self, path, namespace=None, overwrite=True):
        """
        will walk over directory and each class needs to be a model

        when overwrite used it will overwrite the generated models (careful)

        :param path:
        :return: None
        """

        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.toml", followSymlinks=True)
        for schemapath in tocheck:
            dest = "%s/bcdb_model_%s.py" % (j.sal.fs.getDirName(schemapath), j.sal.fs.getBaseName(schemapath, True))
            self.model_add_from_schema(schemapath, dest=dest, overwrite=overwrite, namespace=namespace)

        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.py", followSymlinks=True)
        for classpath in tocheck:
            self.model_add_from_file(classpath)

    def destroy(self):
        """
        delete all objects in the zdb
        :return:
        """
        self.dbclient.destroy()

    def reset(self):
        if self.dbclient.type == "ZDB":
            self.dbclient.reset()
        else:
            for item in self.dbclient.keys("bcdb:*"):
                self.dbclient.delete(item)
        self.reset_index()
