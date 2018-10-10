
from Jumpscale import j

from .BCDB import BCDB
from .BCDBModel import BCDBModel
# from peewee import Model
import gevent
import os
import sys
import time

JSBASE = j.application.JSBaseClass


class BCDBFactory(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.__jslocation__ = "j.data.bcdb"
        self._code_generation_dir = None
        self.bcdb_instances = {}  #key is the name
        self.latest = None

    def get(self, name, dbclient=None,cache=True):
        if dbclient is None:
            dbclient = j.core.db
        if not name in self.bcdb_instances or cache==False:
            if j.data.types.string.check(dbclient):
                raise RuntimeError("zdbclient cannot be str")
            self.bcdb_instances[name] = BCDB(dbclient=dbclient,name=name)
            self.latest = self.bcdb_instances[name]
        return self.bcdb_instances[name]

    def redis_server_start(self,ipaddr="localhost",port=6380,background=False):
        """
        start a redis server on port 6380 on localhost only

        you need to feed it with schema's

        trick: use RDM to investigate (Redis Desktop Manager) to investigate DB.

        js_shell "j.data.bcdb.redis_server_start(background=True)"


        :return:
        """

        if background:
            cmd = 'js_shell "j.data.bcdb.redis_server_start(ipaddr=\'%s\', port=%s)"'%(ipaddr,port)
            j.tools.tmux.execute(
                cmd,
                session='main',
                window='bcdb_server',
                pane='main',
                session_reset=False,
                window_reset=True
            )
            j.sal.nettools.waitConnectionTest(ipaddr=ipaddr, port=port, timeoutTotal=5)
            r = j.clients.redis.get(ipaddr=ipaddr, port=port)
            assert r.ping()

        else:
            dbclient=j.core.db
            bcdb=self.get("test",dbclient=dbclient)
            bcdb.redis_server_start()


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

    @property
    def _path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__))


    def _load_test_model(self,redis=False):

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

        if not redis:
            db_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)
        else:
            db_cl = j.core.db #fall back onto redis

        bcdb = j.data.bcdb.get(name="test",dbclient=db_cl)
        bcdb.reset()
        model = bcdb.model_add_from_schema(schema)

        return bcdb,model

    def test(self,start=True):
        """
        js_shell 'j.data.bcdb.test(start=False)'
        """
        self.test1(start=start)
        self.test2()
        self.test3()
        # self.test4()
        print ("ALL TESTS DONE OK FOR BCDB")

    def test1(self,start=True):
        """
        js_shell 'j.data.bcdb.test1(start=False)'
        """

        def load():


            db,model = self._load_test_model()


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
                print (o2.id, i)
                assert o2.id == i

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

        assert m.index.select().where(m.index.id == 5)[0].name == "name5"
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
            result[obj.id]=obj.name
            return result

        result = m.iterate(do, key_start=0, direction="forward",
                nrrecords=100000, _keyonly=False,
                result={})

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

        result = m.iterate(do, key_start=5, direction="forward",result={})
        assert result == {5: 'name5', 6: 'name6', 7: 'name7', 8: 'name8', 9: 'name9'}

        print ("TEST DONE")

    def test2(self, start=True):
        """
        js_shell 'j.data.bcdb.test2(start=False)'

        this is a test where we use the queuing mechanism for processing data changes

        """

        db, m = self._load_test_model()

        db.gevent_start()

        def get_obj(i):
            o = m.new()
            o.nr = i
            o.name= "somename%s"%i
            return o

        o = get_obj(1)

        #should be empty
        assert m.bcdb.queue.empty() == True

        m.set(o)

        o2 = m.get(o.id)
        assert o2._data == o._data

        #will process 1000 obj (set)
        for x in range(1000):
            m.set(get_obj(x))

        #should be something in queue
        assert m.bcdb.queue.empty() == False

        #now make sure index processed and do a new get
        m.index_ready()

        o2 = m.get(o.id)
        assert o2._data == o._data

        assert m.bcdb.queue.empty()

        j.shell()

        # gevent.sleep(10000)

        # print ("TEST2 DONE, but is still minimal")


    def test3(self, start=True):
        """
        js_shell 'j.data.bcdb.test3(start=False)'
        """

        #make sure we remove the maybe already previously generated model file
        j.sal.fs.remove("%s/tests/models/bcdb_model_test.py"%self._path)

        zdb_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)
        db = j.data.bcdb.get(name="test",dbclient=zdb_cl)
        db.reset_index()

        db.models_add("%s/tests"%self._path,overwrite=True)

        m = db.model_get('jumpscale.bcdb.test.house')

        o = m.new()
        o.cost = "10 USD"

        m.set(o)

        data = m.get(o.id)

        assert data.cost_usd == 10

        assert o.cost_usd == 10

        assert m.index.select().first().cost == 10.0  #is always in usd

        print ("TEST3 DONE, but is still minimal")

    def test4(self):
        """
        js_shell 'j.data.bcdb.test4()'

        this is a test for the redis interface

        """
        self.redis_server_start(background=True)

        r = j.clients.redis.get(ipaddr="localhost", port=6380)

        S = """
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
        """

        r.delete("schemas:despiegk.test")
        r.delete("objects:despiegk.test")

        #there should be 0 objects
        assert r.hlen("objects:despiegk.test") == 0

        r.set("schemas:despiegk.test", S)

        s2=r.get("schemas:despiegk.test")
        #test schemas are same
        assert s2 == S

        schema=j.data.schema.add(S)

        def get_obj(i):
            o = schema.new()
            o.nr = i
            o.name= "somename%s"%i
            o.token_price = "10 EUR"
            return o

        for i in range(10):
            print(i)
            o = get_obj(i)
            id = r.hset("objects:despiegk.test","new",o._json)

        #there should be 10 items now there
        assert r.hlen("objects:despiegk.test") == 10
        assert r.hdel("objects:despiegk.test","10") == 10
        assert r.hlen("objects:despiegk.test") == 9
        assert r.hget("objects:despiegk.test","5") == None
        assert r.hget("objects:despiegk.test",5) == r.hget("objects:despiegk.test","5")

        print("GET")

        json = r.hget("objects:despiegk.test","10")
        json2 = o._json
        assert json == json2

        o.name="UPDATE"
        r.hset("objects:despiegk.test:1",o._json)
        json3 = r.hget("objects:despiegk.test","1")
        json4 = o._json

        assert json != json3 #should have been updated in db, so no longer same
        assert json4 == json3

        j.shell()
