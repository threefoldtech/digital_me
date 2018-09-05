from jumpscale import j
JSBASE = j.application.jsbase_get_class()

model = """
@url = jumpscale.digitalme.package
enabled = false (B)
start = 0 (D)
path = "" (S)
docsites = (LO) !jumpscale.digitalme.package.docsite
blueprints = (LO) !jumpscale.digitalme.package.blueprints
actors = (LO) !jumpscale.digitalme.package.actors
chatflows = (LO) !jumpscale.digitalme.package.chatflow
recipes = (LO) !jumpscale.digitalme.package.recipes
docmacros = (LO) !jumpscale.digitalme.package.docmacros
zrbotrepos = (LO) !jumpscale.digitalme.package.zrbotrepos
models = (LO) !jumpscale.digitalme.package.models

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



class Package(JSBASE):
    def __init__(self,path):
        JSBASE.__init__(self)
        self.path = j.sal.fs.getDirName(path)
        db_client = j.clients.redis_config.get().redis
        self.bcdb = j.data.bcdb.get(db_client)
        schema_model = j.data.bcdb.MODEL_CLASS(bcdb=self.bcdb, schema=model)
        self.bcdb.model_add(schema_model)
        self._model = self.bcdb.model_get(url="jumpscale.digitalme.package")
        self.data = self._model.new()

        data = j.data.serializer.toml.load(path)
        #be flexible
        #std value is False
        if "enable" in data:
            self.data.enabled =data["enable"]
        elif "enabled" in data:
            self.data.enabled =data["enabled"]
        elif "active" in data:
            self.data.enabled =data["enabled"]

        self.data.name = j.sal.fs.getBaseName(self.path)

        dir_items = j.sal.fs.listDirsInDir(self.path,False,True)

        if "actors" in dir_items:
            name = "%s_internal"%(self.name)
            if name not in self.actors:
                obj = self.data.actors.new({"name":name, "enabled":True,
                                            "path":"%s/actors"%(self.path)})

        if "blueprints" in dir_items:
            name = "%s_internal"%(self.name)
            if name not in self.blueprints:
                obj = self.data.blueprints.new({"name":name, "enabled":True,
                                            "path":"%s/blueprints"%(self.path)})

        if "models" in dir_items:
            name = "%s_internal"%(self.name)
            if name not in self.models:
                obj = self.data.models.new({"name":name, "enabled":True,
                                            "path":"%s/models"%(self.path)})

        if "chatflows" in dir_items:
            name = "%s_internal"%(self.name)
            if name not in self.chatflows:
                obj = self.data.chatflows.new({"name":name, "enabled":True,
                                            "path":"%s/chatflows"%(self.path)})

        if "recipes" in dir_items:
            name = "%s_internal"%(self.name)
            if name not in self.recipes:
                obj = self.data.recipes.new({"name":name, "enabled":True,
                                            "path":"%s/recipes"%(self.path)})

        if "doc_macros" in dir_items:
            name = "%s_internal"%(self.name)
            if name not in self.doc_macros:
                obj = self.data.doc_macros.new({"name":name, "enabled":True,
                                            "path":"%s/doc_macros"%(self.path)})

        if "docs" in dir_items:
            name = "%s_internal"%(self.name)
            if name not in self.docsites:
                obj = self.data.docsites.new({"name":name, "enabled":True,
                                            "path":"%s/docs"%(self.path)})

        #TODO: *1 finish & test

        if "docsite" in data:
            for item in data["docsite"]:
                if item["name"] not in self.docsites:
                    obj=self.data.docsites.new(item)
                    obj.path = j.clients.git.getContentPathFromURLorPath(obj.url)

        if "blueprint" in data:
            for item in data["blueprint"]:
                if item["name"] not in self.blueprints:
                    obj = self.data.blueprints.new(item)
                    obj.path = j.clients.git.getContentPathFromURLorPath(obj.url)

        if "chatflows" in data:
            for item in data["chatflows"]:
                if item["name"] not in self.chatflows:
                    obj = self.data.chatflows.new(item)
                    obj.path = j.clients.git.getContentPathFromURLorPath(obj.url)

        if "actors" in data:
            for item in data["actors"]:
                if item["name"] not in self.actors:
                    obj = self.data.actors.new(item)
                    obj.path = j.clients.git.getContentPathFromURLorPath(obj.url)

        if "models" in data:
            for item in data["models"]:
                if item["name"] not in self.models:
                    obj = self.data.models.new(item)
                    obj.path = j.clients.git.getContentPathFromURLorPath(obj.url)

        if "recipes" in data:
            for item in data["recipes"]:
                if item["name"] not in self.recipes:
                    obj = self.data.recipes.new(item)
                    obj.path = j.clients.git.getContentPathFromURLorPath(obj.url)

        if "doc_macros" in data:
            for item in data["doc_macros"]:
                if item["name"] not in self.doc_macros:
                    obj = self.data.doc_macros.new(item)
                    obj.path = j.clients.git.getContentPathFromURLorPath(obj.url)

        #TODO:need to check and make sure we have all see ...threefoldtech/digital_me/packages/readme.md

        self.load()


    @property
    def name(self):
        return self.data.name

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
    def doc_macros(self):
        return [item.name for item in self.data.doc_macros]

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
        rack = j.servers.digitalme.rack
        gedis = j.servers.gedis.latest

        #need to load the blueprints, docsites, actors, ...
        self.chatflows_load()

    def chatflows_load(self):
        for item in self.data.chatflows:
            j.servers.gedis.latest.chatbot.chatflows_load(item.path)
        return
