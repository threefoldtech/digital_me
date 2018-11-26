from Jumpscale import j
JSBASE = j.application.JSBaseClass
import sys
from importlib import import_module

SCHEMA_PACKAGE = """
@url =  jumpscale.digitalme.package
name = "UNKNOWN" (S)           #official name of the package, there can be no overlap (can be dot notation)
enable = true (B)
web_prefixes = "" (LS)
args = (LO) !jumpscale.digitalme.package.arg
loaders= (LO) !jumpscale.digitalme.package.loader

@url =  jumpscale.digitalme.package.arg
key = "" (S)
val =  "" (S)

@url =  jumpscale.digitalme.package.loader
giturl =  "" (S)
dest =  "" (S)
enable = true (B)

##ENDSCHEMA

"""

TOML_KEYS = ["docsite","web","chatflow","actor","schema","recipe","docmacro","zrobotrepo","configobject"]
TOML_KEYS_DIRS = ["docsite","web","zrobotrepo"]


class Package(JSBASE):
    def __init__(self,bcdb,path_config=None,name=None):
        JSBASE.__init__(self)

        self.bcdb=bcdb

        # self._loaded = [] #key is processed by j.core.text.strip_to_ascii_dense
        self.logger_enable()

        if path_config:
            self.toml_load(path_config)
        else:
            if name == None:
                raise RuntimeError("toml path or name has to be specified")
            else:
                #load the data from BCDB
                j.shell()

        self._path = None
        self._loaded = False
        self._args = None

        self.load() #don't do if you want lazy loading, NOT READY FOR THIS YET, but prepared

    def text_replace(self,txt):
        """
        use the args to replace vars in the txt using jinja2
        :param txt:
        :return:
        """
        if self.args != {}:
            return j.tools.jinja2.template_render(path='', text=txt, dest=None, reload=False, **self.args)
        else:
            return txt

    def _error_raise(self,msg,path=""):
        msg_out = "ERROR in package:%s\n"%self.name
        if path!="":
            msg_out+="path:%s\n"%path
        msg_out+= "%s\n"%msg
        raise RuntimeError(msg_out)


    def toml_load(self,path):
        """
        loads the toml and will link all the parts it finds into the destination package directory
        :return:
        """
        if j.sal.fs.isDir(path):
            path+="/dm_package.toml"

        if not j.sal.fs.exists(path):
            self._error_raise("cannot find toml path",path=path)
        #just to check that the toml is working
        try:
            data = j.data.serializers.toml.load(path)
        except Exception as e:
            self._error_raise("toml syntax error",path=path)

        s=j.data.schema.get(SCHEMA_PACKAGE)
        self.data = s.get(data=data)


    def _symlink(self):

        path = self.path
        j.sal.fs.remove(path) #always need to start from empty
        j.sal.fs.createDir(path)

        for loader in self.data.loaders:
            code_path = self.text_replace(j.clients.git.getContentPathFromURLorPath(loader.giturl))
            dest = self.text_replace(loader.dest)
            if dest != "":
                dest = j.sal.fs.joinPaths(path,dest)
                j.sal.fs.symlink(code_path,dest)
            else:
                if not j.sal.fs.exists(code_path):
                    raise RuntimeError("did not find code_path:%s"%code_path)
                for key in TOML_KEYS:
                    src = j.sal.fs.joinPaths(code_path,key)
                    if not j.sal.fs.exists(src):
                        src+="s"
                    # self.logger.debug("scan:%s"%src)
                    if j.sal.fs.exists(src) and j.sal.fs.isDir(src):
                        #found an item we need to link
                        if key in TOML_KEYS_DIRS:
                            #need to link the directories inside
                            for src2 in j.sal.fs.listDirsInDir(src):
                                basename = j.core.text.strip_to_ascii_dense(j.sal.fs.getBaseName(src2)).lower()
                                dest2 = j.sal.fs.joinPaths(path,key+"s",basename)
                                if j.sal.fs.exists(dest2):
                                    self._error_raise("destination exists, cannot link %s to %s"%(src2,dest2))

                                j.sal.fs.symlink(src2,dest2)
                        else:
                            for src2 in  j.sal.fs.listFilesInDir(src):
                                basename = j.sal.fs.getBaseName(src2)
                                dest2 = j.sal.fs.joinPaths(path,key+"s",basename)
                                if j.sal.fs.exists(dest2):
                                    self._error_raise("destination exists, cannot link %s to %s"%(src2,dest2))
                                j.sal.fs.symlink(src2,dest2)


    def load(self):
        if self._loaded:
            return

        self._symlink()

        for key in TOML_KEYS:
            src = j.sal.fs.joinPaths(self.path,key+"s")
            self.logger.debug("load:%s"%src)
            if j.sal.fs.exists(src):
                if key in TOML_KEYS_DIRS:
                    #items are dirs inside
                    for src2 in j.sal.fs.listDirsInDir(src):
                        basename = j.sal.fs.getBaseName(src2)
                        if key == "docsite":
                            dsname="%s_%s"%(self.name,basename)
                            j.tools.docsites.load(src2, dsname)
                        # elif key == "blueprint":
                        #     if self.path not in j.servers.web.latest.loader.paths:
                        #         j.servers.web.latest.loader.paths.append(self.path)
                        elif key == "web":
                            j.servers.openresty.configs_add(src2,args={"path":src2,"name":basename})
                        elif key == "zrobotrepo":
                            j.shell()
                            w
                        else:
                            self._error_raise("wrong dir :%s"%src2)
                else:
                    if key == "schema":
                        self.bcdb.models_add(src)
                        j.servers.gedis.latest.models_add(self.bcdb, namespace=self.name)
                    elif key == "chatflow":
                        j.servers.gedis.latest.chatbot.chatflows_load(src)
                    elif key == "actor":
                        j.servers.gedis.latest.actors_add(src, namespace=self.name)
                    elif key == "recipe":
                        j.shell()
                        w
                    elif key == "docmacro":
                        j.tools.markdowndocs.macros_load(src)
                    else:
                        self._error_raise("wrong dir :%s"%src)

        self._loaded = True

    @property
    def name(self):
        return self.data.name

    @property
    def path(self):
        if self._path is None:
            return j.sal.fs.joinPaths(j.dirs.VARDIR,"dm_packages",self.name)
        return self._path


    @property
    def args(self):
        if self._args is None:
            self._args = {}
            for key,val in self.data.args:
                self._args[key]=val
        return self._args

