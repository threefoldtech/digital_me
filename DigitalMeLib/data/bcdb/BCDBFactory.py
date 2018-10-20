from Jumpscale import j

from .BCDB import BCDB
from .BCDBModel import BCDBModel
# from peewee import Model
import gevent
import os
import sys
import time
import redis

JSBASE = j.application.JSBaseClass


class BCDBFactory(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.__jslocation__ = "j.data.bcdb"
        self._path = j.sal.fs.getDirName(os.path.abspath(__file__))
        self._code_generation_dir = None
        self.bcdb_instances = {}  #key is the name
        self.latest = None
        self.logger_enable()


    def get(self, name, zdbclient=None,cache=True):
        if zdbclient is None:
            #now a generic client on zdb, but needs to become a sqlite version
            zdbclient = j.clients.zdb.client_get(nsname="test", addr="localhost",port=9900,secret="1234",mode="seq")
        if not name in self.bcdb_instances or cache==False:
            if j.data.types.string.check(zdbclient):
                raise RuntimeError("zdbclient cannot be str")
            self.bcdb_instances[name] = BCDB(zdbclient=zdbclient,name=name)
            self.latest = self.bcdb_instances[name]
        return self.bcdb_instances[name]

    def redis_server_start(self,   name="test",
                                   ipaddr="localhost",
                                   port=6380,
                                   background=False,
                                   secret="123456",
                                   zdbclient_addr="localhost",
                                   zdbclient_port=9900,
                                   zdbclient_namespace="test",
                                   zdbclient_secret="1234",
                                   zdbclient_mode="seq",
                                   ):
        """
        start a redis server on port 6380 on localhost only

        you need to feed it with schema's

        trick: use RDM to investigate (Redis Desktop Manager) to investigate DB.

        js_shell "j.data.bcdb.redis_server_start(background=True)"


        :return:
        """

        if background:

            args="ipaddr=\"%s\", "%ipaddr
            args+="name=\"%s\", "%name
            args+="port=%s, "%port
            args+="secret=\"%s\", "%secret
            args+="zdbclient_addr=\"%s\", "%zdbclient_addr
            args+="zdbclient_port=%s, "%zdbclient_port
            args+="zdbclient_namespace=\"%s\", "%zdbclient_namespace
            args+="zdbclient_secret=\"%s\", "%zdbclient_secret
            args+="zdbclient_mode=\"%s\", "%zdbclient_mode


            cmd = 'js_shell \'j.data.bcdb.redis_server_start(%s)\''%args
            j.tools.tmux.execute(
                cmd,
                session='main',
                window='bcdb_server',
                pane='main',
                session_reset=False,
                window_reset=True
            )
            j.sal.nettools.waitConnectionTest(ipaddr=ipaddr, port=port, timeoutTotal=5)
            r = j.clients.redis.get(ipaddr=ipaddr, port=port, password=secret)
            assert r.ping()

        else:
            zdbclient = j.clients.zdb.client_get(nsname=zdbclient_namespace, addr=zdbclient_addr, port=zdbclient_port,
                                                 secret=zdbclient_secret, mode=zdbclient_mode)
            bcdb=self.get(name,zdbclient=zdbclient)
            bcdb.load(zdbclient)
            bcdb.redis_server_start(port=port,secret=secret)



    @property
    def code_generation_dir(self):
        if not self._code_generation_dir:
            path = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "models")
            j.sal.fs.createDir(path)
            if path not in sys.path:
                sys.path.append(path)
            j.sal.fs.touch(j.sal.fs.joinPaths(path, "__init__.py"))
            self.logger.debug("codegendir:%s" % path)
            self._code_generation_dir = path
        return self._code_generation_dir

    @property
    def MODEL_CLASS(self):
        return BCDBModel

    def _load_test_model(self,reset=True):

        schema = """
        @url = despiegk.test
        llist2 = "" (LS)
        name* = ""
        email* = ""
        nr* = 0
        date_start* = 0 (D)
        description = ""
        token_price* = "10 USD" (N)
        cost_estimate:hw_cost = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        llist5 = "1,2,3" (LI)
        U = 0.0
        #pool_type = "managed,unmanaged" (E)  #NOT DONE FOR NOW
        """

        if self.bcdb_instances=={}:
            self.logger.debug("start bcdb in tmux")
            server_db = j.servers.zdb.start_test_instance(reset=reset)
            zdbclient_admin = j.servers.zdb.client_admin_get()
            zdbclient = zdbclient_admin.namespace_new("test",secret="1234")
            bcdb = j.data.bcdb.get(name="test",zdbclient=zdbclient)
            schemaobj=j.data.schema.get(schema)
            bcdb.model_add_from_schema(schemaobj,zdbclient=zdbclient) #model has now been added to the DB
        else:
            bcdb = self.bcdb_instances["test"]

        bcdb.models = {} #just to make sure all is empty, good to test

        self.logger.debug("bcdb already exists")
        zdbclient = j.servers.zdb.client_get("test",secret="1234")
        res = bcdb.load(zdbclient)
        model = bcdb.model_get("despiegk.test")


        if reset:
            zdbclient_admin = j.servers.zdb.client_admin_get()
            model.reset_data(zdbclient_admin,force=True)  #we need a method which allows a user to delete its own data

        assert len(model.zdbclient.meta.schemas_load())==1  #check schema's loaded

        assert model.get_all()==[]

        return bcdb,model

    def test(self):
        """
        js_shell 'j.data.bcdb.test()'
        """
        self.logger_enable()
        self.test1()
        self.test2()
        # self.test3()
        self.test4()
        print ("ALL TESTS DONE OK FOR BCDB")

    def test1(self):
        """
        js_shell 'j.data.bcdb.test1()'
        """

        def load():

            #don't forget the record 0 is always a systems record

            db,model = self._load_test_model()

            assert model.zdbclient.nsinfo["entries"]==1

            for i in range(10):
                o = model.new()
                o.llist.append(1)
                o.llist2.append("yes")
                o.llist2.append("no")
                o.llist3.append(1.2)
                o.date_start = j.data.time.epoch
                o.U = 1.1
                o.nr = i
                o.token_price = "10 EUR"
                o.description = "something"
                o.name = "name%s" % i
                o.email = "info%s@something.com" % i
                o2 = model.set(o)

            o3 = model.get(o2.id)
            assert o3.id == o2.id

            assert o3._ddict == o2._ddict
            assert o3._ddict == o._ddict

            return db

        db = load()

        m = db.model_get(url="despiegk.test")
        query = m.index.select()
        qres = [(item.name, item.nr) for item in query]

        assert qres == [('name0', 0),
             ('name1', 1),
             ('name2', 2),
             ('name3', 3),
             ('name4', 4),
             ('name5', 5),
             ('name6', 6),
             ('name7', 7),
             ('name8', 8),
             ('name9', 9)]

        assert m.index.select().where(m.index.nr == 5)[0].name == "name5"


        query =  m.index.select().where(m.index.nr > 5) # should return 4 records
        qres = [(item.name,item.nr) for item in query]

        assert len(qres) == 4

        res = m.index.select().where(m.index.name=="name2")
        assert len(res) == 1
        assert res.first().name == "name2"

        res = m.index.select().where(m.index.email=="info2@something.com")
        assert len(res) == 1
        assert res.first().name == "name2"

        o = m.get(res.first().id)

        o.name = "name2"

        assert o._changed_items == {}  # because data did not change, was already that data
        o.name = "name3"
        assert o._changed_items ==  {'name': 'name3'}  # now it really changed

        assert o._ddict["name"] == "name3"

        o.token_price = "10 USD"
        assert o.token_price_usd == 10
        m.set(o)
        o2=m.get(o.id)
        assert o2.token_price_usd == 10

        assert m.index.select().where(m.index.id == o.id).first().token_price == 10

        def do(id,obj,result):
            result[obj.nr]=obj.name
            return result

        result = {}
        for obj in m.iterate(key_start=0, reverse=False):
            result[obj.nr] = obj.name

        print (result)
        assert result == {0: 'name0',
             1: 'name1',
             2: 'name3',
             3: 'name3',
             4: 'name4',
             5: 'name5',
             6: 'name6',
             7: 'name7',
             8: 'name8',
             9: 'name9'}

        result = {}
        for obj in m.iterate(key_start=7, reverse=False):
            result[obj.nr] = obj.name
        assert result == {5: 'name5', 6: 'name6', 7: 'name7', 8: 'name8', 9: 'name9'}

        self.logger.info("TEST DONE")

    def test2(self):
        """
        js_shell 'j.data.bcdb.test2()'

        this is a test where we use the queuing mechanism for processing data changes

        """

        db, m = self._load_test_model()

        def get_obj(i):
            o = m.new()
            o.nr = i
            o.name= "somename%s"%i
            return o

        o = get_obj(1)

        #should be empty
        assert m.bcdb.queue.empty() == True

        # j.shell()
        m.set(o)

        o2 = m.get(o.id)
        assert o2._data == o._data

        #will process 1000 obj (set)
        for x in range(1000):
            m.set(get_obj(x))

        #should be nothing in queue
        assert m.bcdb.queue.empty() == True

        #now make sure index processed and do a new get
        m.index_ready()

        o2 = m.get(o.id)
        assert o2._data == o._data

        assert m.bcdb.queue.empty()

        # gevent.sleep(10000)

        self.logger.info("TEST2 DONE")

    # def test3(self, start=True):
    #     """
    #     js_shell 'j.data.bcdb.test3(start=False)'
    #     """
    #
    #     #make sure we remove the maybe already previously generated model file
    #     j.sal.fs.remove("%s/tests/models/bcdb_model_test.py"%self._path)
    #
    #     zdb_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)
    #     db = j.data.bcdb.get(name="test",zdbclient=zdb_cl)
    #     db.reset_index()
    #
    #     db.models_add("%s/tests"%self._path,overwrite=True)
    #
    #     m = db.model_get('jumpscale.bcdb.test.house')
    #
    #     o = m.new()
    #     o.cost = "10 USD"
    #
    #     m.set(o)
    #
    #     data = m.get(o.id)
    #
    #     assert data.cost_usd == 10
    #
    #     assert o.cost_usd == 10
    #
    #     assert m.index.select().first().cost == 10.0  #is always in usd
    #
    #     print ("TEST3 DONE, but is still minimal")

    def test4(self,start=False):
        """
        js_shell 'j.data.bcdb.test4(start=True)'

        this is a test for the redis interface
        """
        if start:
            j.servers.zdb.start_test_instance(reset=True,namespaces=["test"])
            self.redis_server_start(port=6380, background=True)
            j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeoutTotal=5)

        r = j.clients.redis.get(ipaddr="localhost", port=6380)

        S = """
        @url = despiegk.test2
        llist2 = "" (LS)
        name* = ""
        email* = ""
        nr* = 0
        date_start* = 0 (D)
        description = ""
        token_price* = "10 USD" (N)
        cost_estimate:hw_cost = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        """
        S=j.core.text.strip(S)
        self.logger.debug("set schema to 'despiegk.test2'")
        r.set("schemas:despiegk.test2", S)
        self.logger.debug('compare schema')
        s2=r.get("schemas:despiegk.test2")
        #test schemas are same

        assert _compare_strings(S, s2)

        self.logger.debug("delete schema")
        r.delete("schemas:despiegk.test2")
        self.logger.debug("delete data")
        r.delete("objects:despiegk.test2")

        r.set("schemas:despiegk.test2", S)

        self.logger.debug('there should be 0 objects')
        assert r.hlen("objects:despiegk.test2") == 0


        schema=j.data.schema.get(S)

        self.logger.debug("add objects")
        def get_obj(i):
            o = schema.new()
            o.nr = i
            o.name= "somename%s"%i
            o.token_price = "10 EUR"
            return o

        try:
            o = get_obj(0)
            id = r.hset("objects:despiegk.test2", 0, o._json)
            raise RuntimeError("should have raise runtime error when trying to write to index 0")
        except redis.exceptions.ResponseError as err:
            # runtime error is expected when trying to write to index 0
            pass

        for i in range(1, 11):
            # print(i)
            o = get_obj(i)
            id = r.hset("objects:despiegk.test2","new",o._json)

        self.logger.debug("validate list")
        cl=j.clients.zdb.client_get()
        assert cl.list() == [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


        self.logger.debug("validate added objects")
        #there should be 10 items now there
        assert r.hlen("objects:despiegk.test2") == 10
        assert r.hdel("objects:despiegk.test2", 5) == 1
        assert r.hlen("objects:despiegk.test2") == 9
        assert r.hget("objects:despiegk.test2", 5) == None
        assert r.hget("objects:despiegk.test2", 5) == r.hget("objects:despiegk.test2", "5")

        assert cl.list() == [0, 2, 3, 4, 6, 7, 8, 9, 10, 11]

        resp = r.hget("objects:despiegk.test2",i+1)
        json = j.data.serializers.json.loads(resp)
        json2 = j.data.serializers.json.loads(o._json)
        json2['id'] = i+1
        assert json == json2

        self.logger.debug("update obj")
        o.name="UPDATE"
        r.hset("objects:despiegk.test2",11, o._json)
        resp = r.hget("objects:despiegk.test2", 11)
        json3 = j.data.serializers.json.loads(resp)
        assert json3['name'] == "UPDATE"
        json4 = j.data.serializers.json.loads(o._json)
        json4['id'] = 11

        assert json != json3 #should have been updated in db, so no longer same
        assert json4 == json3

        try:
            r.hset("objects:despiegk.test2",1, o._json)
        except Exception as e:
            assert str(e).find("cannot update object with id:1, it does not exist")!=-1
            #should not be able to set because the id does not exist

        #restart redis lets see if schema's are there autoloaded
        self.redis_server_start(port=6380, background=True)
        r = j.clients.redis.get(ipaddr="localhost", port=6380)

        assert r.hlen("objects:despiegk.test2") == 9

        json =  r.hget("objects:despiegk.test2", 3)
        ddict = j.data.serializers.json.loads(json)

        assert ddict == {'name': 'somename2',
             'email': '',
             'nr': 2,
             'date_start': 0,
             'description': '',
             'token_price': '10 EUR',
             'cost_estimate': 0.0,
             'llist2': [],
             'llist': [],
             'llist3': [],
             'llist4': [],
             'id': 3}

        self.logger.debug("clean up database")
        r.delete("objects:despiegk.test2")

        #there should be 0 objects
        assert r.hlen("objects:despiegk.test2") == 0

        cl=j.clients.zdb.client_get()  #need to get new client because namespace removed because of the delete
        assert cl.list() == [0]

        self.logger.debug("TEST OK")


    def test5_populate_data(self,start=False):
        """
        js_shell 'j.data.bcdb.test5_populate_data(start=True)'

        this populates  redis with data so we can test e.g. with RDM (redis desktop manager)
        """
        if start:
            j.servers.zdb.start_test_instance(reset=True,namespaces=["test"])
            self.redis_server_start(port=6380, background=True)
            j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeoutTotal=5)

        r = j.clients.redis.get(ipaddr="localhost", port=6380)

        S = """
        @url = despiegk.test2
        llist2 = "" (LS)
        name* = ""
        email* = ""
        nr* = 0
        date_start* = 0 (D)
        description = ""
        token_price* = "10 USD" (N)
        cost_estimate:hw_cost = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        """
        S=j.core.text.strip(S)
        self.logger.debug("set schema to 'despiegk.test2'")
        r.set("schemas:despiegk.test2", S)
        self.logger.debug('compare schema')
        schema=j.data.schema.get(S)

        self.logger.debug("add objects")
        def get_obj(i):
            o = schema.new()
            o.nr = i
            o.name= "somename%s"%i
            o.token_price = "10 EUR"
            return o

        for i in range(1, 11):
            # print(i)
            o = get_obj(i)
            id = r.hset("objects:despiegk.test2","new",o._json)

        S = """
        @url = another.test
        name* = ""
        nr* = 0
        token_price* = "10 USD" (N)
        """
        S=j.core.text.strip(S)
        self.logger.debug("set schema to 'another.test'")
        r.set("schemas:another.test", S)
        schema=j.data.schema.get(S)
        for i in range(1, 100):
            # print(i)
            o = get_obj(i)
            id = r.hset("objects:another.test","new",o._json)



def _compare_strings(s1, s2):
    # TODO: move somewhere into jumpsclale tree
    def convert(s):
        if isinstance(s, bytes):
            s = s.decode()
        return s

    return convert(s1).strip() == convert(s2).strip()
