from Jumpscale import j

JSBASE = j.application.JSBaseClass


class GedisCmd(JSBASE):
    def __init__(self, namespace, cmd):
        """
        these are the cmds which get executed by the gevent server handler for gedis
        (cmds coming from websockets or redis interface)
        """
        JSBASE.__init__(self)

        self.cmdobj = cmd
        self.data = cmd._data
        self.namespace = namespace
        self.name = cmd.name

        self.schema_in = _load_schema(self.namespace, cmd.name, cmd.schema_in)
        self.schema_out = _load_schema(self.namespace, cmd.name, cmd.schema_out)
        self._method = None

    @property
    def args(self):
        if self.schema_in is None:
            return self.cmdobj.args

        out = ""
        for prop in self.schema_in.properties + self.schema_in.lists:
            d = prop.default_as_python_code
            out += "%s=%s, " % (prop.name, d)
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
            return "," + ','.join(args)
        else:
            if len(self.schema_in.properties + self.schema_in.lists) == 0:
                return ""
            else:
                if len(arguments) == 1 and len(self.schema_in.properties + self.schema_in.lists) > 1:
                    out = ",id=0,"
                else:
                    out = ","
            for prop in self.schema_in.properties + self.schema_in.lists:
                d = prop.default_as_python_code
                out += "%s=%s, " % (prop.name, d)
            out = out.rstrip().rstrip(",").rstrip().rstrip(",")
            return out

    @property
    def args_client_js(self):
        t = self.args_client.strip(",")
        t = t.replace("False", "false")
        t = t.replace("True", "true")
        t = t.replace("**", "...")
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
        return j.core.text.indent(self.cmdobj.comment, nspaces=8).rstrip()

    @property
    def method_generated(self):
        """
        is a real python method, can be called, here it gets loaded & interpreted
        """
        if self._method is None:
            self._method = j.tools.jinja2.code_python_render(
                obj_key="action", path="%s/templates/actor_command_server.py" %
                j.servers.gedis.path, obj=self, objForHash=self._data)
        return self._method

    def __repr__(self):
        return '%s:%s' % (self.namespace, self.name)

    __str__ = __repr__


def _load_schema(namespace, name, schema_str):
    schema = None
    if schema_str:
        if schema_str.startswith("!"):
            url = schema_str.strip("!").strip()
            schema = j.data.schema.get(url=url)
        else:
            schema = j.data.schema.get(schema_str, url=namespace + ".%s.out" % name)
        schema.objclass  # FIXME property with side effects ?
    return schema
