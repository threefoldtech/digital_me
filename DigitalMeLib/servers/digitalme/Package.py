from Jumpscale import j
JSBASE = j.application.JSBaseClass
import sys
from importlib import import_module

SCHEMA_PACKAGE = """
@url = jumpscale.digitalme.package
enabled = false (B)
start = 0 (D)
path = "" (S)
namespace = "" (S)
docsites = (LO) !jumpscale.digitalme.package.docsite
blueprints = (LO) !jumpscale.digitalme.package.blueprints
actors = (LO) !jumpscale.digitalme.package.actors
chatflows = (LO) !jumpscale.digitalme.package.chatflow
recipes = (LO) !jumpscale.digitalme.package.recipes
docmacros = (LO) !jumpscale.digitalme.package.docmacros
zrbotrepos = (LO) !jumpscale.digitalme.package.zrbotrepos
models = (LO) !jumpscale.digitalme.package.models
doc_macros = (LO) !jumpscale.digitalme.package.docmacros

@url = jumpscale.digitalme.package.docsite
name = "" (S)
url = "" (S)
path = "" (S)
publish = "" (S)
enabled = false (B)

@url = jumpscale.digitalme.package.blueprints
name = "" (S)
url = "" (S)
path = "" (S)
publish = (B)
enabled = false (B)
links = (LO) !jumpscale.digitalme.package.bp.link

@url = jumpscale.digitalme.package.bp.link
name = "" (S)
url = "" (S)
dest = "" (S)
enabled = false (B)

@url = jumpscale.digitalme.package.actors
name = "" (S)
url = "" (S)
path = "" (S)
enabled = false (B)

@url = jumpscale.digitalme.package.chatflow
name = "" (S)
url = "" (S)
path = "" (S)
enabled = false (B)

@url = jumpscale.digitalme.package.recipes
name = "" (S)
url = "" (S)
path = "" (S)
enabled = false (B)

@url = jumpscale.digitalme.package.docmacros
name = "" (S)
url = "" (S)
path = "" (S)
enabled = false (B)

@url = jumpscale.digitalme.package.zrbotrepo
name = "" (S)
url = "" (S)
path = "" (S)
enabled = false (B)

@url = jumpscale.digitalme.package.models
name = "" (S)
url = "" (S)
path = "" (S)
enabled = false (B)

"""

TOML_KEYS_ALIASES = {}
TOML_KEYS_ALIASES["enable"] = "enabled"
TOML_KEYS_ALIASES["active"] = "enabled"


class Package(JSBASE):
    def __init__(self,path,zdbclients={}):
        JSBASE.__init__(self)

        self.zdbclients = zdbclients

        #SOMEWHERE IN FUTURE WE WILL HAVE TO STORE THE MODELS IN OWN ZDB
        # self._bcdb_core = j.data.bcdb.get(j.core.db,namespace="system") #get system namespace for own metadata
        # self._bcdb_core.model_create(schema=SCHEMA_PACKAGE)
        # self._model = self._bcdb_core.model_get(url="jumpscale.digitalme.package")

        s=j.data.schema.get(SCHEMA_PACKAGE)
        self.data = s.new()
        self.data.path = j.sal.fs.getDirName(path)

        data = j.data.serializers.toml.load(path)  #path is the toml file

        self.data.namespace = data.get("namespace","default")  #fall back on default value "default" for the namespace

        #each package is part of a namespace

        #be flexible
        #std value is False
        if "enable" in data:
            self.data.enabled =data["enable"]
        elif "enabled" in data:
            self.data.enabled =data["enabled"]
        elif "active" in data:
            self.data.enabled =data["active"]

        self.data.name = j.sal.fs.getBaseName(self.path)

        def find_sub_dir(cat):
            cat = cat.rstrip("s")
            dir_items = j.sal.fs.listDirsInDir(self.path, False, True)
            cat=cat.lower()
            # if self.data.name == "examples" and cat=="docsites":
            #     from pudb import set_trace; set_trace()
            res = []
            for item in dir_items:

                #all elements to check against, category without s, with s, before_
                tocheck = [item.lower(), item.lower().rstrip("s")]
                if "_" in item:
                    item1 = item.split("_",1)[0]
                    tocheck.append(item1.lower())
                    tocheck.append(item1.lower().rstrip("s"))

                for checkitem in tocheck:
                    if checkitem==cat:
                        res.append(j.sal.fs.joinPaths(self.path, item))
            return res

        def get_toml_section(tomldata,cat):
            tocheck = [cat,  cat.lower(),  cat.rstrip("s"), cat.lower().rstrip("s")]
            for itemtocheck in tocheck:
                if itemtocheck in data:
                    return data[itemtocheck]


        #walk over all sections in the toml file
        for cat in ["docsites","blueprints","chatflows","actors","models","recipes","docmacros","blueprint_links"]:

            for subdirpath in  find_sub_dir(cat):
                #we found a subdir which is related to the category
                subdirname = j.sal.fs.getBaseName(subdirpath.rstrip("/"))
                if "_" in subdirname:
                    name=subdirname.split("_",1)[1]
                else:
                    name="main"
                obj = self.obj_get(cat=cat, name=name)
                #now we have the relevant data obj
                obj.path = subdirpath
                obj.name = name
                obj.enabled = True

            tomlsub = get_toml_section(data, cat)
            if tomlsub is not None:
                #we found the subsection in toml

                for item in tomlsub:
                    if "name" not in item:
                        name = "main"
                    else:
                        name = item["name"]
                    if cat == 'blueprint_links':
                        self._process_link("main",item)
                    else:
                        obj = self.obj_get(cat, name)
                        obj.name = name
                        if "path" in item:
                            obj.path = item["path"]
                        elif "url" in item:
                            obj.path = j.clients.git.getContentPathFromURLorPath(item["url"])
                            obj.url = item["url"]
                        else:
                            raise RuntimeError("did not find path or url in %s,%s" % (item, self))
                        #now look for keys in the toml item out of default, need to add those too
                        for key in item.keys():
                            if key not in ["path","name","url"]:
                                key2 = self._key_toml(key)
                                obj._changed_items[key2] = item[key]
                                # obj._data


        # if "blueprint_links" in data:
        #     for item in data["blueprint_links"]:
        #         j.shell()
        #         w
        #         staticpath = j.clients.git.getContentPathFromURLorPath(
        #             "https://github.com/threefoldtech/jumpscale_weblibs/tree/master/static")
        #
        #         # create link to static dir on jumpscale web libs
        #         localstat_path = "%s/static" % j.sal.fs.getDirName(__file__)
        #         # j.sal.fs.remove(localstat_path)
        #         j.sal.process.execute("rm -f %s" % localstat_path)  # above does not work if link is broken in advance
        #         j.sal.fs.symlink(staticpath, localstat_path, overwriteTarget=True)


        if self.data.enabled:
            #only when enabled load the stuff in mem
            self.load()



    def _key_toml(self,key):
        if key in TOML_KEYS_ALIASES:
            return TOML_KEYS_ALIASES[key]
        return key

    def _process_link(self,name,toml):
        if "path" in toml:
            path = toml["path"]
        elif "url" in toml:
            path = j.clients.git.getContentPathFromURLorPath(toml["url"])
        obj = self.obj_get("blueprints",name=name)
        if obj.path=="":
            raise RuntimeError("did not find blueprint with name:%s in %s"(name,self))
        sobj = obj.links.new()
        target = j.sal.fs.joinPaths(obj.path,toml["name"],toml["dest"])
        sobj.dest = target
        sobj.url = toml["url"]
        sobj.enabled = True
        j.sal.fs.symlink(path, target, overwriteTarget=True)


    @property
    def name(self):
        return self.data.name

    @property
    def namespace(self):
        return self.data.namespace

    @property
    def path(self):
        return self.data.path


    @property
    def docsites(self):
        return [item.name for item in self.data.docsites]

    @property
    def blueprints(self):
        return [item.name for item in self.data.blueprints]

    @property
    def chatflows(self):
        return [item.name for item in self.data.chatflows]

    @property
    def docmacros(self):
        return [item.name for item in self.data.docmacros]

    @property
    def zrobot_repos(self):
        return [item.name for item in self.data.zrobot_repos]

    @property
    def actors(self):
        return [item.name for item in self.data.actors]

    @property
    def models(self):
        return [item.name for item in self.data.models]

    def load(self):
        """
        load package into memory
        """
        # rack = j.servers.digitalme.rack
        # gedis = j.servers.gedis.latest

        #need to load the blueprints, docsites, actors, ...
        self.chatflows_load()
        self.blueprints_load()
        self.docsites_load()
        self.models_load()
        self.docmacros_load()
        self.actors_load()


    def obj_get(self,cat="blueprints",name="main"):
        itemslist = getattr(self.data, cat)
        for item in itemslist:
            if item.name == name:
                return item
        return itemslist.new()


    def models_load(self):
        #fetch the right client for the right BCDB
        for item in self.data.models:
            if not self.namespace in j.data.bcdb.bcdb_instances:
                if self.namespace in self.zdbclients:
                    zdbclient = self.zdbclients[self.namespace]
                else:
                    if "default" not in self.zdbclients:
                        raise RuntimeError("default zdb client not specified")
                    zdbclient = self.zdbclients["default"]
                j.data.bcdb.bcdb_instances[self.namespace] = j.data.bcdb.get(name=self.namespace, zdbclient=zdbclient)
            bcdb = j.data.bcdb.bcdb_instances[self.namespace]
            bcdb.models_add(item.path)


    def chatflows_load(self):
        for item in self.data.chatflows:
            j.servers.gedis.latest.chatbot.chatflows_load(item.path)
        return

    def blueprints_load(self):
        for blueprint in self.data.blueprints:
            if blueprint.enabled:
                j.servers.web.latest.loader.paths.append(blueprint.path)

    def docsites_load(self):
        for doc_site in self.data.docsites:
            j.tools.docsites.load(doc_site.path, doc_site.name)

    def docmacros_load(self):
        # if self.namespace=="threefold":
        #     from pudb import set_trace; set_trace()
        for item in self.data.docmacros:
            j.tools.docsites.macros_load(item.path)

    def actors_load(self):
        for item in self.data.actors:
            j.servers.gedis.latest.actors_add(item.path, namespace=self.namespace)
