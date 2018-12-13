from Jumpscale import j

JSBASE = j.application.JSBaseClass
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

TOML_KEYS = ["docsites", "web", "chatflows", "actors", "schemas", "recipes", "docmacros", "zrobotrepo", "configobject"]
TOML_KEYS_DIRS = ["docsites", "web", "zrobotrepo"]


class Package(JSBASE):
    def __init__(self, bcdb, path_config=None, name=None):
        """Initialize a package object

        If path_config is provided it loads it the package from this path.
        If name is provided, it retrieves it from bcdb

        :param bcdb: bcdb instance used to save/load package data
        :type bcdb: BCDB class
        :param path_config: path to load the package from, defaults to None
        :type path_config: string, optional
        :param name: package name, defaults to None
        :type name: string, optional
        :raises RuntimeError: if neither path_config nor name was provided
        """
        JSBASE.__init__(self)
        if not path_config and not name:
            raise RuntimeError("Either toml path or name has to be specified")

        self.bcdb = bcdb
        self.logger_enable()
        self.data = dict()
        if path_config:
            self.toml_load(path_config)
        else:
            # @TODO: load the data from BCDB
            pass

        if self.name.find('.') != -1:
            raise RuntimeError("Package name can't contain dots")

        self._path = None
        self._loaded = False
        self._args = None

        self.load()  # don't do if you want lazy loading, NOT READY FOR THIS YET, but prepared

    def text_replace(self, txt):
        """Use the package args to replace vars in the txt using jinja2

        :param txt: the text containing vars to be substituted
        :type txt: string
        :return: txt after variable substitution
        :rtype: string
        """
        if self.args != {}:
            return j.tools.jinja2.template_render(path="", text=txt, dest=None, reload=False, **self.args)
        else:
            return txt

    def _error_raise(self, msg, path=""):
        """Helper function for formatting errors and raisiong a RuntimeError while loading the package

        :param msg: error message
        :type msg: string
        :param path: the path relevant to the error, defaults to ""
        :param path: str, optional
        :raises RuntimeError: raise the error with the formatted message
        """
        msg_out = "ERROR in package:%s\n" % self.name
        if path != "":
            msg_out += "path:%s\n" % path
        msg_out += "%s\n" % msg
        raise RuntimeError(msg_out)

    def toml_load(self, path):
        """loads the package configuration file dm_package.toml into the package data
        using the package schema

        :param path: package or configuration file path
        :type path: string
        """
        if j.sal.fs.isDir(path):
            path += "/dm_package.toml"

        if not j.sal.fs.exists(path):
            raise RuntimeError("%s not found" % path)
        # just to check that the toml is working
        try:
            data = j.data.serializers.toml.load(path)
        except Exception as e:
            raise RuntimeError("Syntax error in %s" % path)

        s = j.data.schema.get(SCHEMA_PACKAGE)
        self.data = s.get(data=data)

    def _symlink(self):
        """Use the package loader sections in the configuration to symlink the relevant files
        under self.path

        :raises RuntimeError: raises RuntimeError if any of the destinations exist
        """
        path = self.path
        j.sal.fs.remove(path)  # always need to start from empty
        j.sal.fs.createDir(path)

        for loader in self.data.loaders:
            code_path = self.text_replace(j.clients.git.getContentPathFromURLorPath(loader.giturl))
            if not j.sal.fs.exists(code_path):
                raise RuntimeError("did not find code_path:%s" % code_path)

            dest = self.text_replace(loader.dest)
            if dest != "":
                dest = j.sal.fs.joinPaths(path, dest)
                if j.sal.fs.exists(dest):
                    self._error_raise("destination exists, cannot link %s to %s" % (code_path, dest))
                j.sal.fs.symlink(code_path, dest)

            else:
                for key in TOML_KEYS:
                    src = j.sal.fs.joinPaths(code_path, key)
                    if j.sal.fs.exists(src) and j.sal.fs.isDir(src):
                        # found an item we need to link
                        if key in TOML_KEYS_DIRS:
                            # need to link the directories inside
                            for src2 in j.sal.fs.listDirsInDir(src):
                                basename = j.core.text.strip_to_ascii_dense(j.sal.fs.getBaseName(src2)).lower()
                                dest2 = j.sal.fs.joinPaths(path, key, basename)
                                if j.sal.fs.exists(dest2):
                                    self._error_raise("destination exists, cannot link %s to %s" % (src2, dest2))

                                j.sal.fs.symlink(src2, dest2)
                        else:
                            for src2 in j.sal.fs.listFilesInDir(src):
                                basename = j.sal.fs.getBaseName(src2)
                                dest2 = j.sal.fs.joinPaths(path, key, basename)
                                if j.sal.fs.exists(dest2):
                                    self._error_raise("destination exists, cannot link %s to %s" % (src2, dest2))
                                j.sal.fs.symlink(src2, dest2)

    def load(self):
        """Load the package by linking the files and loading docsites, web, schemas, actors, chatflows and docmacros
        """
        if self._loaded:
            return

        self._symlink()

        for key in TOML_KEYS:
            src = j.sal.fs.joinPaths(self.path, key)
            self.logger.debug("load:%s" % src)
            if j.sal.fs.exists(src):
                if key in TOML_KEYS_DIRS:
                    # items are dirs inside
                    for src2 in j.sal.fs.listDirsInDir(src):
                        basename = j.sal.fs.getBaseName(src2)
                        if key == "docsites":
                            dsname = "%s_%s" % (self.name, basename)
                            j.tools.docsites.load(src2, dsname)
                        elif key == "web":
                            j.servers.openresty.configs_add(src2, args={"path": src2, "name": basename})
                        elif key == "zrobotrepo":
                            pass
                        else:
                            self._error_raise("wrong dir :%s" % src2)
                else:
                    if key == "schemas":
                        self.bcdb.models_add(src)
                        j.servers.gedis.latest.models_add(self.bcdb, namespace=self.name)
                    elif key == "chatflows":
                        j.servers.gedis.latest.chatbot.chatflows_load(src)
                    elif key == "actors":
                        j.servers.gedis.latest.actors_add(src, namespace=self.name)
                    elif key == "recipes":
                        pass
                    elif key == "docmacros":
                        j.tools.markdowndocs.macros_load(src)
                    else:
                        self._error_raise("wrong dir :%s" % src)

        self._loaded = True

    @property
    def name(self):
        return self.data.name

    @property
    def path(self):
        if self._path is None:
            return j.sal.fs.joinPaths(j.dirs.VARDIR, "dm_packages", self.name)
        return self._path

    @property
    def args(self):
        if self._args is None:
            self._args = {}
            for key, val in self.data.args:
                self._args[key] = val
        return self._args
