from Jumpscale import j
JSBASE = j.application.JSBaseClass
import sys
from importlib import import_module

SCHEMA_PACKAGE = """
@url =  jumpscale.digitalme.package
name = "UNKNOWN" (S)           #official name of the package, there can be no overlap (can be dot notation)
enable = true (B)
args = (LO) !jumpscale.digitalme.package.arg
actors_loader= (LO) !jumpscale.digitalme.package.items_loader
actors = (LO) !jumpscale.digitalme.package.item
docsites_loader= (LO) !jumpscale.digitalme.package.items_loader
docsites = (LO) !jumpscale.digitalme.package.item
blueprints_loader= (LO) !jumpscale.digitalme.package.items_loader
blueprints = (LO) !jumpscale.digitalme.package.item
links = (LO) !jumpscale.digitalme.package.link
chatflows_loader= (LO) !jumpscale.digitalme.package.items_loader
chatflows = (LO) !jumpscale.digitalme.package.item
schemas_loader= (LO) !jumpscale.digitalme.package.items_loader
schemas = (LO) !jumpscale.digitalme.package.item
recipes_loader= (LO) !jumpscale.digitalme.package.items_loader
recipes = (LO) !jumpscale.digitalme.package.item
zrobot_repos_loader= (LO) !jumpscale.digitalme.package.items_loader
docmacros_loader= (LO) !jumpscale.digitalme.package.items_loader
docmacros = (LO) !jumpscale.digitalme.package.item
configobjects_loader= (LO) !jumpscale.digitalme.package.items_loader
configobjects = (LO) !jumpscale.digitalme.package.item



@url =  jumpscale.digitalme.package.arg
key = "" (S)
val =  "" (S)

@url =  jumpscale.digitalme.package.items_loader
giturl =  "" (S)
enable = true (B)

@url =  jumpscale.digitalme.package.item
instance = "" (S)
prefix = "" (S)
path = "" (S)
enable = true (B)

@url =  jumpscale.digitalme.package.link
giturl =  "" (S)
dest = "" (S)
enable = true (B)


##ENDSCHEMA

"""

TOML_KEYS_ALIASES = {}
TOML_KEYS_ALIASES["enabled"] = "enable"
TOML_KEYS_ALIASES["active"] = "enable"

TOML_KEYS = ["docsites","blueprints","chatflows","actors","schemas","recipes","docmacros","links","zrobot_repos","configobjects"]

class Package(JSBASE):
    def __init__(self,bcdb):
        JSBASE.__init__(self)

        self.bcdb = bcdb
        s=j.data.schema.get(SCHEMA_PACKAGE)
        self.data = s.new()
        self._loaded = [] #key is processed by j.core.text.strip_to_ascii_dense

    def _error_raise(self,msg,path=""):
        msg = "ERROR in package:%s\n"%self.data.name
        if path!="":
            msg+="path:%s\n"%path
        msg+= "%s\n"%msg
        raise RuntimeError(msg)



    def load(self):
        """
        the loaders are there to find more info & include it
        this loader will make sure the directories are pulled in from github & info inside processed
        :return:
        """

        j.shell()


    def toml_add(self,path,category="schema"):
        if not j.sal.fs.exists(path):
            self._error_raise("cannot find toml path",path=path)
        #just to check that the toml is working
        try:
            data = j.data.serializers.toml.load(path)
        except Exception as e:
            j.shell()
            self._error_raise("toml syntax error",path=path)
        j.shell()

        def get_toml_section(tomldata,cat):
            tocheck = [cat,  cat.lower(),  cat.rstrip("s"), cat.lower().rstrip("s")]
            for itemtocheck in tocheck:
                if itemtocheck in data:
                    return data[itemtocheck]



    def path_scan(self,path):

        path_norm = j.core.text.strip_to_ascii_dense(path)
        if path_norm not in self._loaded:

            j.shell()

            # self.data.path = j.sal.fs.getDirName(path)

            data = j.data.serializers.toml.load(path)  #path is the toml file

            self.data.namespace = data.get("namespace","default")  #fall back on default value "default" for the namespace

            #each package is part of a namespace

            #be flexible
            #std value is False
            if "enable" in data:
                self.data.enable =data["enable"]
            elif "enable" in data:
                self.data.enable =data["enable"]
            elif "active" in data:
                self.data.enable =data["active"]

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



            #walk over all sections in the toml file
            for cat in ["docsites","blueprints","chatflows","actors","models","recipes","docmacros","links"]:

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
                    obj.enable = True

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
                                obj.giturl =  item["url"]
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


            if self.data.enable:
                #only when enable load the stuff in mem
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
        sobj.giturl =  toml["url"]
        sobj.enable = True
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

        if not self.namespace in j.data.bcdb.bcdb_instances:
            if self.namespace in self.zdbclients:
                zdbclient = self.zdbclients[self.namespace]
            else:
                if "default" not in self.zdbclients:
                    raise RuntimeError("default zdb client not specified")
                zdbclient = self.zdbclients["default"]
            j.data.bcdb.bcdb_instances[self.namespace] = j.data.bcdb.new(name=self.namespace, zdbclient=zdbclient)
        bcdb = j.data.bcdb.bcdb_instances[self.namespace]

        for item in self.data.models:
            bcdb.models_add(path=item.path)

        j.servers.gedis.latest.models_add(bcdb, namespace=self.namespace)


    def chatflows_load(self):
        for item in self.data.chatflows:
            j.servers.gedis.latest.chatbot.chatflows_load(item.path)
        return

    def blueprints_load(self):
        for blueprint in self.data.blueprints:
            if blueprint.enable:
                j.servers.web.latest.loader.paths.append(blueprint.path)

    def docsites_load(self):
        for doc_site in self.data.docsites:
            j.tools.docsites.load(doc_site.path, doc_site.name)

    def docmacros_load(self):
        # if self.namespace=="threefold":
        #     from pudb import set_trace; set_trace()
        for item in self.data.docmacros:
            j.tools.markdowndocs.macros_load(item.path)

    def actors_load(self):
        for item in self.data.actors:
            j.servers.gedis.latest.actors_add(item.path, namespace=self.namespace)
