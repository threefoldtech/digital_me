
from Jumpscale import j
import inspect
import imp

import os

JSBASE = j.application.JSBaseClass

class GedisCmd(JSBASE):
    def __init__(self,cmds,cmd):
        """
        these are the cmds which get executed by the gevent server handler for gedis (cmds coming from websockets or redis interface)
        """
        JSBASE.__init__(self)

        self.cmdobj = cmd
        self.data = cmd._data
        self.cmds = cmds
        self.server = self.cmds.server
        self.name = cmd.name

        if not cmd.schema_in.strip()=="":
            if cmd.schema_in.startswith("!"):
                url=cmd.schema_in.strip("!").strip()
                self.schema_in = j.data.schema.get(url=url)
            else:
                self.schema_in=j.data.schema.get(cmd.schema_in,url=self.namespace+".%s.in"%cmd.name)
            self.schema_in.objclass
        else:
            self.schema_in = None

        if cmd.schema_out:
            if cmd.schema_out.startswith("!"):
                url=cmd.schema_out.strip("!").strip()
                self.schema_out = j.data.schema.get(url=url)
            else:
                self.schema_out = j.data.schema.get(cmd.schema_out,url=self.namespace+".%s.out"%cmd.name)
            self.schema_out.objclass
        else:
            self.schema_out = None

        self._method = None

        # print(self.code_runtime)



    @property
    def namespace(self):
        return self.cmds.data.namespace

    @property
    def args(self):
        if self.schema_in==None:
            return self.cmdobj.args
        else:
            out= ""
            for prop in self.schema_in.properties + self.schema_in.lists:
                d=prop.default_as_python_code
                out += "%s=%s, "%(prop.name,d)
            out = out.rstrip().rstrip(",").rstrip()
            out += ",schema_out=None"
            return out

    @property
    def args_client(self):
        arguments = [a.strip() for a in self.cmdobj.args.split(',')]

        if 'schema_out' in arguments:
            arguments.remove('schema_out')

        if self.schema_in is None:
            if self.cmdobj.args.strip() == "":
                return ""
            args = eval(self.cmdobj.args)
            if ':' in args:
                args.remove(':')
            return ","+ ','.join(args)
        else:
            if len(self.schema_in.properties + self.schema_in.lists)==0:
                return ""
            else:
                if len(arguments) == 1 and len(self.schema_in.properties + self.schema_in.lists) > 1:
                    out = ",id=0,"
                else:
                    out = ","
            for prop in  self.schema_in.properties + self.schema_in.lists:
                d=prop.default_as_python_code
                out += "%s=%s, "%(prop.name,d)
            out = out.rstrip().rstrip(",").rstrip().rstrip(",")
            return out

    @property
    def args_client_js(self):
        t = self.args_client.strip(",")
        t = t.replace("False", "false")
        t = t.replace("True", "true")
        t = t.replace("*", "...")
        if t.strip() == ",schema_out":
            return ""
        return t


    @property
    def code_indent(self):
        return j.core.text.indent(self.cmdobj.code)

    @property
    def comment_indent(self):
        return j.core.text.indent(self.cmdobj.comment).rstrip()

    @property
    def comment_indent2(self):
        return j.core.text.indent(self.cmdobj.comment,nspaces=8).rstrip()

    @property
    def method_generated(self):
        """
        is a real python method, can be called, here it gets loaded & interpreted
        """
        if self._method is None:
            j.shell()
            self._method =j.tools.jinja2.code_python_render( obj_key="action",
                                path="%s/templates/actor_command_server.py"%j.servers.gedis.path,obj=self,
                                objForHash=self._data)
        return self._method

    def __repr__(self):
        return '%s:%s' % (str(self.cmds).rstrip(".py"),self.name)

    __str__ = __repr__
