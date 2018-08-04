

from jumpscale import j

JSBASE = j.application.jsbase_get_class()

class system(JSBASE):
    
    def __init__(self):
        JSBASE.__init__(self)
        self.server = j.servers.gedis.latest

    def ping(self):
        return "PONG"

    def ping_bool(self):
        return True

    def core_schemas_get(self):
        """
        return all core schemas as understood by the server, is as text, can be processed by j.data.schema

        """
        res = {}        
        for key,item in j.data.schema.schemas.items():
            res[key] = item.text
        return j.data.serializer.msgpack.dumps(res)

    def api_meta(self):
        """
        return the api meta information

        """  
        s=self.server.cmds_meta
        res={}
        res["namespace"] = self.server.instance
        res["cmds"]={}
        for key,item in s.items():
            res["cmds"][key] = item.data.data
        return j.data.serializer.msgpack.dumps(res)

    def schema_urls(self):
        """
        return the api meta information

        """  
        s=self.server.schema_urls
        return j.data.serializer.msgpack.dumps(s)

    def filemonitor_paths(self,schema_out):
        """
        return all paths which should be monitored for file changes
        ```out
        paths = (LS)        
        ```
        """

        r = schema_out.new()

        #monitor changes for the docsites (markdown)
        for key,item in j.tools.markdowndocs.docsites.items():
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

        #now check if path is in docsites, if yes then reload that docsite only !
        #then check if path is actor if yes, reload that one
        #then check if schema change is yes, reload
        #then check if blueprint, reload blueprint
        #then let websocket subscribers know that their page changed (so we can hot reload a page in browser, through javascript trick)

        print("IMPLEMENT: TODO: filemonitor_event")
        print(changeobj)

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

