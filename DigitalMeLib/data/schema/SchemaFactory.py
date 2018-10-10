
from Jumpscale import j

JSBASE = j.application.JSBaseClass

from .Schema import *
from .List0 import List0
import sys


class SchemaFactory(JSBASE):
    def __init__(self):
        self.__jslocation__ = "j.data.schema"
        JSBASE.__init__(self)
        self._template_engine = None
        self._code_generation_dir = None
        self.db = j.clients.redis.core_get()
        self.schemas = {}
        self._schema_md5_to_schemaurl = {}

    @property
    def SCHEMA_CLASS(self):
        return Schema

    @property
    def code_generation_dir(self):
        if not self._code_generation_dir:
            path = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "schema")
            j.sal.fs.createDir(path)
            if path not in sys.path:
                sys.path.append(path)
            j.sal.fs.touch(j.sal.fs.joinPaths(path, "__init__.py"))
            self.logger.debug("codegendir:%s" % path)
            self._code_generation_dir = path
        return self._code_generation_dir

    def reset(self):
        self.schemas = {}

    def get(self,url=None, die=True):
        url = url.lower().strip()
        if url in self.schemas:
            return self.schemas[url]
        if die:
            raise RuntimeError("could not find schema with url:%s"%url)

    def exists(self,url):
        return self.get(url=url, die=False) is not None

    def add(self, schema=None, first=True):
        """
        can be the url of the schema

        schema can be text
        can also be a path of a schema file

        :param schema_text or schema_path or schema_url
        :return: schema(s)
        """
        if j.data.types.string.check(schema):
            if "\n" not in schema and j.sal.fs.exists(schema):
                schema_text = j.sal.fs.fileGetContents(schema)
            else:
                schema_text = schema
        else:
            if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
                raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")
            schema_text = schema.text

        schema_text2 = j.core.text.strip(schema_text)
        md5 = j.data.hash.md5_string(schema_text2)

        if not md5 in self._schema_md5_to_schemaurl:
            res = self._add(schema_text)
            self._schema_md5_to_schemaurl[md5] = res #remember schemas

        if first:
            return self._schema_md5_to_schemaurl[md5][0]
        else:
            return self._schema_md5_to_schemaurl[md5]


    def _add(self, txt):
        """
        add schema text (can be multile blocks starting with @) to this class
        result schema's can be found from self.schema_from_url(...)

        only the first one will be returned

        """
        block = ""
        state = "start"
        res=[]
        for line in txt.split("\n"):

            l=line.lower().strip()

            if block=="":
                if l == "" or l.startswith("#"):
                    continue

            if l.startswith("@url"):
                if block is not "":
                    s = Schema(text=block)
                    self.schemas[s.url] = s
                    res.append(s)
                block = ""

            block += "%s\n" % line

        if block != "":
            s = Schema(text=block)
            self.schemas[s.url] = s
            res.append(s)

        return res



    def list_base_class_get(self):
        return List0

    def test(self):
        """
        js_shell 'j.data.schema.test()'
        """
        self.test1()
        self.test2()
        self.test3()
        self.test4()

    def test1(self):
        """
        js_shell 'j.data.schema.test1()'
        """
        schema = """
        @url = despiegk.test
        llist2 = "" (LS) #L means = list, S=String        
        nr = 4
        date_start = 0 (D)
        description = ""
        token_price = "10 USD" (N)
        cost_estimate:hw_cost = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        llist5 = "1,2,3" (LI)
        U = 0.0
        #pool_type = "managed,unmanaged" (E)  #NOT DONE FOR NOW
        """

        s = j.data.schema.add(schema)

        print (s)

        o = s.get()

        o.llist.append(1)
        o.llist2.append("yes")
        o.llist2.append("no")
        o.llist3.append(1.2)
        o.llist4.append(1)
        o.llist5.append(1)
        o.llist5.append(2)
        o.U = 1.1
        o.nr = 1
        o.token_price = "10 USD"
        o.description = "something"


        usd2usd = o.token_price_usd # convert USD-to-USD... same value
        assert usd2usd == 10
        inr = o.token_price_cur('inr')
        #print ("convert 10 USD to INR", inr)
        assert inr > 100 # ok INR is pretty high... check properly in a bit...
        eur = o.token_price_eur
        #print ("convert 10 USD to EUR", eur)
        cureur = j.clients.currencylayer.cur2usd['eur']
        curinr = j.clients.currencylayer.cur2usd['inr']
        #print (cureur, curinr, o.token_price)
        assert usd2usd*cureur == eur
        assert usd2usd*curinr == inr

        # try EUR to USD as well
        o.token_price = "10 EUR"
        assert o.token_price == b'\x000\n\x00\x00\x00'
        eur2usd = o.token_price_usd
        assert eur2usd*cureur == 10

        o._cobj

        schema = """
        @url = despiegk.test2
        llist2 = "" (LS)
        nr = 4
        date_start = 0 (D)
        description = ""
        token_price = "10 USD" (N)
        cost_estimate:hw_cost = 0.0 #this is a comment
        llist = []

        @url = despiegk.test3
        llist = []
        description = ""
        """
        j.data.schema.add(schema)
        s1 = self.get(url="despiegk.test2")
        s2 = self.get(url="despiegk.test3")

        o1 = s1.get()
        o2 = s2.get()
        o2.llist.append("1")

        print("TEST 1 OK")

    def test2(self):
        """
        js_shell 'j.data.schema.test2()'
        """
        schema0 = """
        @url = despiegk.test.group
        description = ""
        llist = "" (LO) !despiegk.test.users
        listnum = "" (LI)
        """

        schema1 = """
        @url = despiegk.test.users
        nr = 4
        date_start = 0 (D)
        description = ""
        token_price = "10 USD" (N)
        cost_estimate:hw_cost = 0.0 (N) #this is a comment
        """

        s1 = self.add(schema1)
        s0 = self.add(schema0)
        print(s0)
        o = s1.get()


        print(s1.capnp_schema)
        print(s0.capnp_schema)
        

        print("TEST 2 OK")


    def test3(self):
        """
        js_shell 'j.data.schema.test3()'

        simple embedded schema

        """
        SCHEMA = """
        @url = jumpscale.schema.test3.cmd
        name = ""
        comment = ""
        schemacode = ""

        @url = jumpscale.schema.test3.serverschema
        cmds = (LO) !jumpscale.schema.test3.cmdbox

        @url = jumpscale.schema.test3.cmdbox
        @name = GedisServerCmd1
        cmd = (O) !jumpscale.schema.test3.cmd
        cmd2 = (O) !jumpscale.schema.test3.cmd
        
        """
        self.add(SCHEMA)
        s2 = self.get("jumpscale.schema.test3.serverschema")
        s3 = self.get("jumpscale.schema.test3.cmdbox")

        o = s2.get()
        for i in range(4):
            oo = o.cmds.new()
            oo.name = "test%s"%i

        assert o.cmds[2].name=="test2" 
        o.cmds[2].name="testxx"
        assert o.cmds[2].name=="testxx" 

        bdata = o._data

        o2 = s2.get(capnpbin=bdata)

        assert o._ddict == o2._ddict

        print (o._data)

        o3 = s3.get()
        o3.cmd.name = "test"
        o3.cmd2.name = "test"
        assert o3.cmd.name == "test"
        assert o3.cmd2.name == "test"

        bdata = o3._data
        o4 = s3.get(capnpbin=bdata)
        assert o4._ddict == o3._ddict

        assert o3._data == o4._data

        print("TEST 3 OK")

    def test4(self):
        """
        js_shell 'j.data.schema.test4()'

        tests an issue with lists, they were gone at one point after setting a value

        """

        S0 = """
        @url = jumpscale.schema.test3.cmd
        name = ""
        comment = ""        
        nr = 0
        """
        self.add(S0)

        SCHEMA = """
        @url = jumpscale.myjobs.job
        category*= ""
        time_start* = 0 (D)
        time_stop = 0 (D)
        state* = ""
        timeout = 0
        action_id* = 0
        args = ""   #json
        kwargs = "" #json
        result = "" #json
        error = ""
        return_queues = (LS)
        cmds = (LO) !jumpscale.schema.test3.cmd
        cmd = (O) !jumpscale.schema.test3.cmd
        
        """
        s = self.add(SCHEMA)
        o = s.new()
        o.return_queues = ["a", "b"]
        assert o._return_queues.pylist() == ["a", "b"]
        assert o._return_queues._inner_list == ["a", "b"]
        assert o.return_queues == ["a", "b"]

        o.return_queues[1] = "c"
        assert o._return_queues.pylist() == ["a", "c"]
        assert o._return_queues._inner_list == ["a", "c"]
        assert o.return_queues == ["a", "c"]

        o.return_queues.pop(0)
        assert o._return_queues.pylist() == ["c"]
        assert o._return_queues._inner_list == ["c"]
        assert o.return_queues == ["c"]

        cmd = o.cmds.new()
        cmd.name = "aname"
        cmd.comment = "test"
        cmd.nr = 10

        o.cmd.name = "aname2"
        o.cmd.nr = 11

        o.category = "acategory"

        o1 = {'category': 'acategory',
                 'time_start': 0,
                 'time_stop': 0,
                 'state': '',
                 'timeout': 0,
                 'action_id': 0,
                 'args': '',
                 'kwargs': '',
                 'result': '',
                 'error': '',
                 'cmd': {'name': 'aname2', 'comment': '', 'nr': 11},
                 'return_queues': ['c'],
                 'cmds': [{'name': 'aname', 'comment': 'test', 'nr': 10}]}


        assert o._ddict == o1

        o._data
        o._json

        assert o._ddict == o1

        o2 = s.get(capnpbin= o._data)

        assert o._ddict == o2._ddict
        assert o._data == o2._data


        print ("TEST4 ok")


