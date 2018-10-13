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
from gevent.event import Event
from .BCDBDecorator import *
from gevent import queue
from JumpscaleLib.clients.zdb.ZDBClientBase import ZDBClientBase
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
        self.zdbclient.meta  # make sure record 0 has been set

        self.models = {}

        self._sqlitedb = None
        self._data_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb")

        self._models_add_cache = {}

        self.logger_enable()

        self.zdbclient.meta.schemas_load()

        self.results={}
        self.results_id = 0

        self.dataprocessor_greenlet = None
        self.dataprocessor_start()

        self.logger.info("BCDB INIT DONE:%s"%self.name)

    def redis_server_start(self):

        self.redis_server = RedisServer(bcdb=self)
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

    # def dataprocessor_stop(self):
    #     """
    #     means we stop using the data processor, if you want to pause use self.dataprocessor_pause
    #     :return:
    #     """
    #     if self.dataprocessor_state in ["RUNNING"]:
    #         evt = Event()
    #         self.queue.put(("STOP",evt))
    #         self.logger.debug("wait dataprocessor stop")
    #         evt.wait()


    # def dataqueue_waitempty(self):
    #     """
    #     do not forget to call this before doing a search on index
    #     this will make sure the index is fully populated
    #     will wait till all objects are processed by indexer (the greenlet which processes the data, only 1 per bcdb)
    #     :return: True when empty
    #     """
    #     if self.dataprocessor_data_processing:
    #         counter = 1
    #         while len(self.objects_in_queue) > 0:
    #             gevent.sleep(0.001)
    #             counter += 1
    #             if counter == 10000:
    #                 raise RuntimeError("should never take this long to index, something went wrong")
    #     return True


    @queue_method
    def reset(self):
        self.stop()
        j.shell()

    # @queue_method
    # def stop(self):
    #     self._sqlitedb.close()
    #     if self.name in j.data.bcdb.bcdb_instances:
    #         j.data.bcdb.bcdb_instances.pop(self.name)
    #     # for model in self.models.values():
    #     #     j.shell()
    #     self.dataprocessor_stop()

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

    def reset_index(self):
        for model in self.models.values():
            model.index_delete()
        # self._sqlitedb=None
        # j.sal.fs.remove(self._data_dir)

    def reset_data(self,zdbclient_admin):
        """
        remove index, walk over all zdb's & remove data
        :param zdbclient_admin:
        :return:
        """
        self.logger.info("reset data")
        for model in self.models.values():
            model.reset_data(zdbclient_admin=zdbclient_admin,force=True) #need to always remove


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

    def model_add_from_schema(self, schema, zdbclient, reload=False, dest=None, overwrite=True):
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

        m = self.model_add_from_file(dest, zdbclient=zdbclient)

        self._models_add_cache[schema.md5] = m

        m.zdbclient.meta.schema_set(schema)  # should always be the first record !

        return m

    def model_add_from_file(self, path, zdbclient):
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

        model = model_module.Model(bcdb=self, zdbclient=zdbclient)

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

    def load(self,zdbclient):
        return zdbclient.meta.models_load(self)
