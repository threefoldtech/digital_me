import imp

from Jumpscale import j
from .SchemaProperty import SchemaProperty

JSBASE = j.application.jsbase_get_class()
import copy
import os

class Schema(JSBASE):
    def __init__(self, text=None, url=""):
        JSBASE.__init__(self)
        self.properties = []
        self.lists = []
        self._template = None
        self._capnp_template = None
        self._obj_class = None
        self._capnp = None
        self.hash = ""
        self._index_list = None
        self._SCHEMA = True
        if url:
            self.url = url
        else:
            self.url = ""
            
        self.name = ""
        if text:
            self._schema_from_text(text)

    @property
    def _path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__))


    def error_raise(self,msg,e=None,schema=None):

        if self.url == "" and "url" in self._systemprops:
            self.url =  self._systemprops["url"]
        out="\nerror in schema:\n"
        out+="    url:%s\n"%self.url
        out+="    msg:%s\n"%j.data.text.prefix("    ",msg)
        if schema:
            out+="    schema:\n%s"%schema
        if e is not None:
            out+="\nERROR:\n"
            out+=j.data.text.prefix("        ",str(e))
        raise RuntimeError(out)

    def _proptype_get(self, txt):

        if "\\n" in txt:
            jumpscaletype = j.data.types.multiline
            defvalue = jumpscaletype.fromString(txt)

        elif "'" in txt or "\"" in txt:
            jumpscaletype = j.data.types.string
            defvalue = jumpscaletype.fromString(txt)

        elif "." in txt:
            jumpscaletype = j.data.types.float
            defvalue = jumpscaletype.fromString(txt)

        elif "true" in txt.lower() or "false" in txt.lower():
            jumpscaletype = j.data.types.bool
            defvalue = jumpscaletype.fromString(txt)

        elif "[]" in txt:
            jumpscaletype = j.data.types._list()
            jumpscaletype.SUBTYPE = j.data.types.string
            defvalue = []

        elif j.data.types.int.checkString(txt):
            jumpscaletype = j.data.types.int
            defvalue = jumpscaletype.fromString(txt)

        else:
            raise RuntimeError("cannot find type for:%s" % txt)

        return (jumpscaletype, defvalue)

    def _schema_from_text(self, schema):
        self.logger.debug("load schema:\n%s" % schema)

        self.text = j.data.text.strip(schema)

        self.hash = j.data.hash.blake2_string(schema)

        systemprops = {}
        self.properties = []
        self._systemprops = systemprops

        def process(line):
            line_original = copy.copy(line)
            propname, line = line.split("=", 1)
            propname = propname.strip()
            line = line.strip()
            

            if "!" in line:
                line, pointer_type = line.split("!", 1)
                pointer_type = pointer_type.strip()
                line=line.strip()
            else:
                pointer_type = None

            if "#" in line:
                line, comment = line.split("#", 1)
                line = line.strip()
                comment = comment.strip()
            else:
                comment = ""

            if "(" in line:
                line_proptype = line.split("(")[1].split(")")[0].strip().lower()
                line_wo_proptype = line.split("(")[0].strip()
                if line_proptype=="o": #special case where we have subject directly attached
                    jumpscaletype = j.data.types.get("jo")
                    jumpscaletype.SUBTYPE = pointer_type
                    defvalue = ""
                else:
                    jumpscaletype = j.data.types.get(line_proptype)
                    try:
                        defvalue = jumpscaletype.fromString(line_wo_proptype)
                    except Exception as e:
                        self.error_raise("error on line:%s"%line_original,e=e)                        
            else:
                jumpscaletype, defvalue = self._proptype_get(line)

            if ":" in propname:
                # self.logger.debug("alias:%s"%propname)
                propname, alias = propname.split(":", 1)
            else:
                alias = propname

            if alias[-1]=="*":
                alias=alias[:-1]

            if propname in ["id"]:
                self.error_raise("do not use 'id' in your schema, is reserved for system.",schema=schema)

            return (propname, alias, jumpscaletype, defvalue, comment, pointer_type)

        nr = 0
        for line in schema.split("\n"):
            line = line.strip()
            self.logger.debug("L:%s" % line)
            nr += 1
            if line.strip() == "":
                continue
            if line.startswith("@"):
                systemprop_name = line.split("=")[0].strip()[1:]
                systemprop_val = line.split("=")[1].strip()
                systemprops[systemprop_name] = systemprop_val.strip("\"").strip("'")
                continue
            if line.startswith("#"):
                continue
            if "=" not in line:
                self.error_raise("did not find =, need to be there to define field",schema=schema)

            propname, alias, jumpscaletype, defvalue, comment, pointer_type = process(line)

            p = SchemaProperty()

            if propname.endswith("*"):
                propname=propname[:-1]
                p.index=True

            p.name = propname
            p.default = defvalue
            p.comment = comment
            p.jumpscaletype = jumpscaletype
            p.alias = alias
            p.pointer_type = pointer_type

            if p.jumpscaletype.NAME is "list":
                self.lists.append(p)
            else:
                self.properties.append(p)

        for key, val in systemprops.items():
            self.__dict__[key] = val

        nr=0
        for s in self.properties:
            s.nr = nr
            self.__dict__["property_%s" % s.name] = s
            nr+=1

        for s in self.lists:
            s.nr = nr
            self.__dict__["property_%s" % s.name] = s
            nr+=1


    @property
    def capnp_id(self):
        if self.hash=="":
            raise RuntimeError("hash cannot be empty")
        return "f"+self.hash[1:16]  #first bit needs to be 1

    def _code_template_render(self,**args):
        tpath = "%s/templates/template_obj.py"%self._path
        return j.tools.jinja2.file_render(tpath, write=False, dest=None, **args)

    def _capnp_template_render(self,**args):
        tpath = "%s/templates/schema.capnp"%self._path
        return j.tools.jinja2.file_render(tpath, write=False, dest=None, **args)


    @property
    def code(self):
        #make sure the defaults render
        for prop in self.properties:
            prop.default_as_python_code
        for prop in self.lists:
            prop.default_as_python_code
        code = self._code_template_render(obj=self)
        return code

    @property
    def capnp_schema_text(self):
        return self._capnp_template_render(obj=self)

    @property
    def capnp_schema(self):
        if not self._capnp:
            self._capnp =  j.data.capnp.getSchemaFromText(self.capnp_schema_text)
        return self._capnp

    @property
    def objclass(self):
        if self._obj_class is None:
            url = self.url.replace(".","_")
            path = j.sal.fs.joinPaths(j.data.schema.code_generation_dir, "%s.py" % url)
            j.sal.fs.writeFile(path,self.code)
            m=imp.load_source(name="url", pathname=path)
            self._obj_class = m.ModelOBJ
        return self._obj_class

    def get(self,data=None,capnpbin=None):
        if data is None:
            data = {}
        obj =  self.objclass(schema=self,data=data,capnpbin=capnpbin)
        return obj

    def new(self):
        """
        same as self.get() but with no data
        """
        return self.get()

    @property
    def index_list(self):
        if self._index_list==None:
            self._index_list = []
            for prop in self.properties:
                if prop.index:
                    self._index_list.append(prop.alias)
        return self._index_list

    @property
    def index_properties(self):
        _index_list = []
        for prop in self.properties:
            if prop.index:
                _index_list.append(prop)
        return _index_list
            
    def __str__(self):
        out=""
        for item in self.properties:
            out += str(item) + "\n"
        for item in self.lists:
            out += str(item) + "\n"
        return out

    __repr__=__str__
