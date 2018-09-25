from importlib import import_module
from Jumpscale import j
import sys
from peewee import *
import os
JSBASE = j.application.JSBaseClass
from redis import StrictRedis
from .BCDBIndexModel import BCDBIndexModel


class BCDB(JSBASE):
    
    def __init__(self,dbclient,namespace="default",reset=False,json_serialize=False):
        JSBASE.__init__(self)
        if isinstance(dbclient,j.clients.redis.REDIS_CLIENT_CLASS) or isinstance(dbclient,StrictRedis):
            dbclient.type = "RDB" #means is redis db
        else:
            dbclient.type = "ZDB"

        self.dbclient = dbclient
        self.namespace = namespace
        self.models = {}

        self.index_create(reset=reset)
        if reset:
            if self.dbclient.type == "ZDB":
                pass
            else:
                for item in self.dbclient.keys("bcdb:*"):
                    self.dbclient.delete(item)

        self.json_serialize = json_serialize
        self.index_readonly = False

    def index_create(self,reset=False):
        j.sal.fs.createDir(j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb"))
        dest = j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb",self.namespace+".db")
        self.logger.debug("bcdb:indexdb:%s"%dest)
        if reset:
            j.sal.fs.remove(dest)
        try:
            self.sqlitedb = SqliteDatabase(dest)
        except Exception as e:
            j.shell()

    def model_create(self, schema,dest=None, include_schema=True, overwrite=True):
        """
        :param include_schema, if True schema is added to generated code
        :param schema: j.data.schema ...
        :param dest: optional path where the model should be generated, if not specified will be in codegeneration dir
        :return: model
        """
        if j.data.types.string.check(schema):
            if j.sal.fs.exists(schema):
                schema_text = j.sal.fs.fileGetContents(schema)
            else:
                schema_text = schema
            schema = j.data.schema.schema_add(schema_text)
        else:
            if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
                raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")
            schema_text = schema.text

        imodel = BCDBIndexModel(schema=schema)
        imodel.enable = True
        imodel.include_schema = include_schema
        tpath = "%s/templates/Model.py"%j.data.bcdb._path
        key = j.core.text.strip_to_ascii_dense(schema.url).replace(".","_")
        schema.key = key

        if dest is None:
            dest = "%s/model_%s.py" % (j.data.bcdb.code_generation_dir, key)

        if overwrite or not j.sal.fs.exists(dest):
            self.logger.debug("render model:%s"%dest)
            if dest is None:
                raise RuntimeError("cannot be None")
            j.tools.jinja2.file_render(tpath, write=True, dest=dest, schema=schema,
                                       schema_text=schema_text, bcdb=self, index=imodel)

        return self.model_add(dest)

    def model_add(self,model_or_path):
        """
        add model to BCDB
        can be from a class or from path
        is path to python file

        """
        if isinstance(model_or_path, j.data.bcdb.MODEL_CLASS):
            self.models[model_or_path.schema.url] = model_or_path
        elif j.sal.fs.exists(model_or_path):
            model_or_path = self._model_add_from_path(model_or_path)
        else:
            raise RuntimeError("model needs to be of type: j.data.bcdb.MODEL_CLASS or path to model.")
        return model_or_path

    def models_add(self,path,overwrite=True):
        """
        will walk over directory and each class needs to be a model

        when overwrite used it will overwrite the generated models (careful)

        :param path:
        :return: None
        """

        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.toml", followSymlinks=True)
        for schemapath in tocheck:
            dest = "%s/bcdb_model_%s.py"%(j.sal.fs.getDirName(schemapath),j.sal.fs.getBaseName(schemapath, True))
            self.model_create(schemapath,dest=dest,overwrite=overwrite)


        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.py", followSymlinks=True)
        for classpath in tocheck:
            self.model_add(classpath)

    def _model_add_from_path(self,classpath):
        """
        actual place where we load the python class in mem, never done by enduser
        :param classpath:
        :return:
        """
        dpath = j.sal.fs.getDirName(classpath)
        if dpath not in sys.path:
            sys.path.append(dpath)
            j.sal.fs.touch("%s/__init__.py" % dpath)
        # self.logger.info("model all:%s" % classpath)
        modulename = j.sal.fs.getBaseName(classpath)[:-3]
        if modulename.startswith("_"):
            return
        try:
            self.logger.info("import module:%s" % modulename)
            model_module = import_module(modulename)
            self.logger.debug("ok")
        except Exception as e:
            # j.shell()
            raise RuntimeError("could not import module:%s in classpath:%s" % (modulename,classpath), e)
        model = model_module.Model(bcdb=self)
        self.models[model.schema.url] = model
        return model


    def model_get(self, url):
        if url in self.models:
            return self.models[url]
        raise RuntimeError("could not find model for url:%s"%url)

    def destroy(self):
        """
        delete all objects in the zdb
        :return:
        """
        self.dbclient.destroy()
