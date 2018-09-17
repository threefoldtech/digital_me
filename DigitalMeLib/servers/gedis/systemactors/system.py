

from Jumpscale import j

JSBASE = j.application.JSBaseClass

class system(JSBASE):
    
    def __init__(self):
        JSBASE.__init__(self)
        self.server = j.servers.gedis.latest

    def ping(self):
        return "PONG"

    def auth(self,secret,namespace=""):
        secret = secret.decode()
        #check admin secret
        if self.server.config.data["adminsecret_"]==secret:
            return "OK"

        j.shell()
        return "AUTHERROR"

    def ping_bool(self):
        return True

    def core_schemas_get(self,namespace):
        """
        return all core schemas as understood by the server, is as text, can be processed by j.data.schema

        """
        namespace = namespace.decode()
        res = {}
        for key,item in j.data.schema.schemas.items():
            #TODO: should prob limit to namespace
            res[key] = item.text
        return j.data.serializers.msgpack.dumps(res)

    def api_meta(self,namespace):
        """
        return the api meta information

        """
        namespace = namespace.decode()
        res = {}
        res["cmds"]={}
        for key,item in self.server.cmds_meta.items():
            if item.namespace == namespace:
                res["cmds"][key] = item.data._data
        return j.data.serializers.msgpack.dumps(res)

    def schema_urls(self,*args):
        """
        return the api meta information

        """  
        s=self.server.schema_urls
        return j.data.serializers.msgpack.dumps(s)

    def filemonitor_paths(self,schema_out):
        """
        return all paths which should be monitored for file changes
        ```out
        paths = (LS)        
        ```
        """

        r = schema_out.new()

        #monitor changes for the docsites (markdown)
        for key,item in j.tools.docsites.docsites.items():
            r.paths.append(item.path)

        #monitor change for the webserver  (schema's are in there)
        r.paths.append(j.servers.web.latest.path)

        #changes for the actors
        r.paths.append(j.servers.gedis.latest.code_generated_dir)
        r.paths.append(j.servers.gedis.latest.app_dir+"/actors")
        r.paths.append("%s/systemactors"%j.servers.gedis.path)
        
        return r

    def filemonitor_event(self,changeobj):
        """
        used by filemonitor daemon to escalate events which happened on filesystem

        ```in
        src_path = (S)
        event_type = (S)
        is_directory = (B)        
        ```

        """

        # Check if a blueprint is changed
        # if changeobj.is_directory:
        #     path_parts = changeobj.src_path.split('/')
        #     if path_parts[-2] == 'blueprints':
        #         blueprint_name = "{}_blueprint".format(path_parts[-1])
        #         bp = j.servers.web.latest.app.app.blueprints.get(blueprint_name)
        #         if bp:
        #             self.logger.info("reloading blueprint : {}".format(blueprint_name))
        #             del (j.servers.web.latest.app.app.blueprints[blueprint_name])
        #             j.servers.web.latest.app.app.register_blueself.logger.info(bp)
        #             return

        # Check if docsite is changed
        if changeobj.is_directory:
            docsites = j.tools.docsites.docsites
            for _, docsite in docsites.items():
                if docsite.path in changeobj.src_path:
                    docsite.load()
                    self.logger.info("reloading docsite: {}".format(docsite))
                    return

        # check if path is actor if yes, reload that one
        if not changeobj.is_directory and changeobj.src_path.endswith('.py'):
            paths = list()
            paths.append(j.servers.gedis.latest.code_generated_dir)
            paths.append(j.servers.gedis.latest.app_dir + "/actors")
            paths.append("%s/systemactors" % j.servers.gedis.path)
            # now check if path is in docsites, if yes then reload that docsite only !
            for path in paths:
                if path in changeobj.src_path:
                    actor_name = j.sal.fs.getBaseName(changeobj.src_path)[:-3].lower()
                    namespace = j.servers.gedis.latest.instance + '.' + actor_name
                    if namespace in j.servers.gedis.latest.cmds_meta:
                        del (j.servers.gedis.latest.cmds_meta[namespace])
                        del (j.servers.gedis.latest.classes[namespace])
                        for cmd in list(j.servers.gedis.latest.cmds.keys()):
                            if actor_name in cmd:
                                del (j.servers.gedis.latest.cmds[cmd])
                        j.servers.gedis.latest.cmds_add(namespace, path=changeobj.src_path)
                        self.logger.info("reloading namespace: {}".format(namespace))
                        return

        return

    def test(self,name,nr,schema_out):      
        """
        some test method, which returns something easy

        ```in
        name = ""
        nr = 0 (I)
        ```

        ```out
        name = ""
        nr = 0 (I)
        list_int = (LI)        
        ```

        """  
        o=schema_out.new()
        o.name = name
        o.nr = nr
        # o.list_int = [1,2,3]

        return o

    def test_nontyped(self,name,nr):
        return [name,nr]

    def get_web_client(self):
        return j.servers.gedis.latest.web_client_code

