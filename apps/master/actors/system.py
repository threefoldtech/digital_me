

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

    def docsite_paths(self,schema_out):
        """
        ```out
        paths = (LS)        
        ```
        """
        r = schema_out.new()
        for key,item in j.tools.markdowndocs.docsites.items():
            r.paths.append(item.path)
        return r

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

