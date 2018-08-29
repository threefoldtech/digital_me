
from jumpscale import j

from .BCDB import BCDB
from .BCDBModel import BCDBModel
from peewee import Model
import os
import sys
JSBASE = j.application.jsbase_get_class()


class BCDBFactory(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.__jslocation__ = "j.data.bcdb"
        self._code_generation_dir = None

    def get(self, zdbclient):       
        if j.data.types.string.check(zdbclient):
            raise RuntimeError("zdbclient cannot be str")
        return BCDB(zdbclient)

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
    def PEEWEE_INDEX_CLASS(self):
        db = j.data.bcdb.latest.sqlitedb
        class BaseModel(Model):
            class Meta:
                database = db
            def __repr__(self):
                return (self.__dict__)
            __str__ = __repr__
        return BaseModel

    @property
    def _path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__))


    def test(self,start=True):
        """
        js_shell 'j.data.bcdb.test(start=False)'
        """

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


        def load(start):
    
            zdb_cl = j.clients.zdb.testdb_server_start_client_get(reset=start)
            db = j.data.bcdb.get(zdb_cl)
            db.index_create(reset=start)

            model = db.model_create(schema=schema)

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
                assert o2.id == i

            o3 = model.get(o2.id)
            assert o3.id == o2.id

            assert o3._ddict == o2._ddict
            assert o3._ddict == o._ddict

            return db

        db = load(start=start)

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
        assert o._changed_prop == False  # because data did not change, was already that data
        o.name = "name3"
        assert o._changed_prop == True  # now it really changed

        assert o._ddict["name"] == "name3"

        o.token_price = "10 USD"
        import pudb; pudb.set_trace()
        m.set(o)

        assert m.index.select().where(m.index.id == o.id).first().token_price == 10

        self.test2()

        print ("TEST DONE")

    def test2(self, start=True):
        """
        js_shell 'j.data.bcdb.test2(start=False)'
        """


        zdb_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)
        db = j.data.bcdb.get(zdb_cl)
        db.index_create(reset=True)

        db.models_add("%s/tests"%self._path,overwrite=True)

        m = db.model_get('jumpscale.bcdb.test.house2')

        o = m.new()
        o.cost = "10 USD"

        m.set(o)

        data = m.get(o.id)

        assert data.cost_usd == 10

        assert o.cost_usd == 10

        print ("TEST2 DONE, but is still minimal")
