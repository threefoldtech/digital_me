from importlib import import_module
from Jumpscale import j
import sys
from peewee import *
import os
JSBASE = j.application.jsbase_get_class()

from .BCDBIndexModel import BCDBIndexModel


class BCDB(JSBASE):
    
    def __init__(self,zdbclient):
        JSBASE.__init__(self)
        self.zdbclient = zdbclient
        self.models = {}
        self.logger_enable()

        self.index_create()
        j.data.bcdb.latest = self

    def index_create(self,reset=False):
        j.sal.fs.createDir(j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb"))
        dest = j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb",self.zdbclient.instance+".db")
        j.sal.fs.remove(dest) #TODO:*1 is temporary untill some bugs are fixed
        self.sqlitedb = SqliteDatabase(dest)


    def model_create(self, schema,dest=None, include_schema=True):
        """
        :param include_schema, if True schema is added to generated code
        :param schema: j.data.schema ...
        :param dest: optional path where the model should be generated, if not specified will be in codegeneration dir
        :return: model
        """
        if j.data.types.string.check(schema):
            schema = j.data.schema.schema_add(schema)
        else:
            if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
                raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")
        imodel = BCDBIndexModel(schema=schema)
        imodel.enable = True
        imodel.include_schema = include_schema
        tpath = "%s/templates/Model.py"%j.data.bcdb._path
        key = j.data.text.strip_to_ascii_dense(schema.url).replace(".","_")
        if dest is None:
            dest = "%s/model_%s.py"%(j.data.bcdb.code_generation_dir,key)
        self.logger.debug("render model:%s"%dest)
        j.tools.jinja2.file_render(tpath, write=True, dest=dest, schema=schema, index=imodel)
        return self.model_add(dest)

    def model_add(self,model_or_path):
        """
        add model to BCDB
        """
        if isinstance(model_or_path, j.data.bcdb.MODEL_CLASS):
            self.models[model_or_path.schema.url] = model_or_path
        elif j.sal.fs.exists(model_or_path):
            model_or_path = self._model_add_from_path(model_or_path)
        else:
            raise RuntimeError("model needs to be of type: j.data.bcdb.MODEL_CLASS or path to model.")
        return model_or_path

    def models_add(self,path,overwrite=False):
        """
        will walk over directory and each class needs to be a model

        when overwrite used it will overwrite the generated models (careful)

        :param path:
        :return: None
        """

        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.toml", followSymlinks=True)
        for schemapath in tocheck:
            dest = "%s/%s.py"%(j.sal.fs.getDirName(schemapath),j.sal.fs.getBaseName(schemapath, True))
            if overwrite or not j.sal.fs.exists(dest):
                self.model_create(schemapath,dest=dest)

        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.py", followSymlinks=True)
        for classpath in tocheck:
            self.model_add(classpath)

    def _model_add_from_path(self,classpath):
        dpath = j.sal.fs.getDirName(classpath)
        if dpath not in sys.path:
            sys.path.append(dpath)
            j.sal.fs.touch("%s/.__init__.py" % dpath)
        # self.logger.info("model all:%s" % classpath)
        modulename = j.sal.fs.getBaseName(classpath)[:-3]
        try:
            self.logger.info("import module:%s" % modulename)
            model_module = import_module(modulename)
            self.logger.debug("ok")
        except Exception as e:
            raise RuntimeError("could not import module:%s" % modulename, e)
        model = model_module.Model(self)
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
        self.zdbclient.destroy()
