
from Jumpscale import j
import inspect
# import imp
import sys
import os
from .GedisCmd import GedisCmd

JSBASE = j.application.JSBaseClass


class GedisCmds(JSBASE):
    """
    cmds understood by gedis server
    """
    
    def __init__(self, server=None, namespace="default", name="", path="", capnpbin=None):
        JSBASE.__init__(self)

        if path is "" and capnpbin==None:
            raise RuntimeError("path cannot be None")

        self.namespace = namespace

        self.path=path

        self.server = server

        SCHEMA = """
        @url = jumpscale.gedis.cmd
        @name = GedisCmds
        name = ""
        comment = ""
        code = "" 
        schema_in = ""
        schema_out = ""
        args = ""

        @url = jumpscale.gedis.api
        @name = GedisServerSchema
        namespace = ""
        cmds = (LO) !jumpscale.gedis.cmd  
        """
        j.data.schema.schema_add(SCHEMA)
        self.schema = j.data.schema.schema_get(url="jumpscale.gedis.api")

        self._cmds = {}

        if capnpbin:
            self.data = self.schema.get(capnpbin=capnpbin)
        else:

            dname = j.sal.fs.getDirName(path)
            cname = j.sal.fs.getBaseName(path)[:-3]
            if dname not in sys.path:
                sys.path.append(dname)
            classname = self._class_find_name()
            exec("from %s import %s" % (cname, classname))
            class_ = eval(classname)

            if namespace in cname and cname.startswith("model"):
                cname = "model_%s" % cname.split(namespace, 1)[1].strip("_")
            key="%s__%s"%(self.namespace,cname)

            self.server.classes[key] = class_()

            self.data = self.schema.new()
            self.data.name = name
            self.data.namespace = self.namespace

            for name,item in inspect.getmembers(class_):
                if name.startswith("_"):
                    continue
                if name.startswith("logger"):
                    continue
                if name in ["cache"]:
                    continue
                if inspect.isfunction(item):
                    cmd = self.data.cmds.new()
                    cmd.name = name
                    code = inspect.getsource(item)
                    cmd.code,cmd.comment,cmd.schema_in, cmd.schema_out, cmd.args= self._method_source_process(code)


    @property
    def name(self):
        return self.data.name

    @property
    def cmds(self):
        if self._cmds == {}:
            print('\n\nPopulating commands for namespace(%s)\n' % self.data.namespace)
            for cmd in self.data.cmds:
                print("\tpopulata: %s"%(cmd.name))
                self._cmds[cmd.name] = GedisCmd(self,cmd)
            print('\n')
        return self._cmds

    def _class_find_name(self):
        txt = j.sal.fs.fileGetContents(self.path)
        for line in txt.split("\n"):
            if line.strip().startswith("class"):
                pre = line.split("(")[0]
                classname = pre.split(" ")[1].strip()
                return classname
        raise RuntimeError("did not find class name in %s"%self.path)

    def _method_source_process(self,txt):
        """
        return code,comment,schema_in, schema_out
        """
        txt=j.core.text.strip(txt)
        code = ""
        comment = ""
        schema_in = ""
        schema_out = ""
        args = ""

        state="START"

        for line in txt.split("\n"):
            lstrip = line.strip().lower()
            if state=="START" and lstrip.startswith("def"):
                state = "DEF"
                if "self" in lstrip:
                    if "," in lstrip:
                        arg0,arg1=lstrip.split(",",1)
                        args = arg1.split(")",1)
                    else:
                        args = ""
                else:
                    arg0,arg1=lstrip.split("(",1)
                    args = arg1.split(")",1)
                continue
            if lstrip.startswith("\"\"\""):
                if state=="DEF":
                    state="COMMENT"
                    continue
                if state=="COMMENT":
                    state="CODE"
                    continue
                raise RuntimeError()
            if lstrip.startswith("```") or lstrip.startswith("'''"):
                if state.startswith("SCHEMA"): #are already in schema go back to comment
                    state="COMMENT"
                    continue
                if state=="COMMENT": #are in comment, now found the schema
                    if lstrip.endswith("out"):
                        state="SCHEMAO"
                    else:
                        state="SCHEMAI"
                    continue
                raise RuntimeError()
            if state=="SCHEMAI":
                schema_in+="%s\n"%line
                continue
            if state=="SCHEMAO":
                schema_out+="%s\n"%line
                continue
            if state=="COMMENT":
                comment+="%s\n"%line
                continue
            if state=="CODE" or state=="DEF":
                code+="%s\n"%line
                continue
            raise RuntimeError()
        return j.core.text.strip(code),j.core.text.strip(comment),j.core.text.strip(schema_in),\
            j.core.text.strip(schema_out),args
            

    def cmd_exists(self,name):
        return name in self.children
    

    def __repr__(self):
        path2 = self.path.split("github")[-1].strip("/")
        return 'CMDS:%s' % (path2)

    __str__ = __repr__


