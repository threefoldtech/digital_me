# from gevent import monkey
# monkey.patch_all()

import inspect
from Jumpscale import j
import gipc
import gevent
import time
from .MyWorker import  myworker

JSBASE = j.application.JSBaseClass

schema_job = """
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


"""

schema_action = """
@url = jumpscale.myjobs.action
key* = ""  #hash
code = ""
methodname = ""


"""


schema_worker = """
@url = jumpscale.myjobs.worker
timeout = 3600
time_start = 0 (D)
last_update = 0 (D) 
current_job = (I)
halt = false (B)
running = false (B)
pid = 0

"""


class MyJobs(JSBASE):
    """
    """

    def __init__(self):
        self.__jslocation__ = "j.servers.myjobs"
        JSBASE.__init__(self)
        self.queue = j.clients.redis.getQueue(redisclient=j.core.db, name="myjobs", fromcache=True)
        self.queue_data = j.clients.redis.getQueue(redisclient=j.core.db, name="myjobs_datachanges", fromcache=False)
        self._init = False
        self.workers = {}
        self.workers_nr_min = 1
        self.workers_nr_max = 10
        self.mainloop = None
        self.dataloop = None
        self.logger_enable()

    def init(self,reset=False):
        """

        :param db_cl: if None will use db_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)
        :return:
        """
        if self._init == False:

            if reset:
                self.halt(reset=True)

            db = j.data.bcdb.get(j.core.db, namespace="myjobs", reset=reset,json_serialize=True)

            self.model_job = db.model_create(schema=schema_job)
            self.model_action = db.model_create(schema=schema_action)
            self.model_worker = db.model_create(schema=schema_worker)
            self._init = True


    def action_get(self,key,return_none_if_not_exist=False):
        self.init()
        res = self.model_action.index.select().where(self.model_action.index.key == key).execute()
        if len(res) > 0:
            o = self.model_action.get(res[0].id)
            return False,o
        else:
            if return_none_if_not_exist:
                return
            o = self.model_action.new()
            return True,o


    @property
    def nr_workers(self):
        return len(self.workers.values())

    def start(self,onetime=False):
        """

        :param nr_max: max nr of workers which can be started
        :return:
        """
        self._worker_start(onetime=onetime) #start first worker
        if onetime:
            self._data_process(onetime=True)
            self._main_loop(onetime=True)
        else:
            self.mainloop = gevent.spawn(self._main_loop)
            self.dataloop = gevent.spawn(self._data_process)
            self.mainloop.start()
            self.dataloop.start()

    def _worker_start(self,onetime=False):
        w = self.model_worker.new()
        w.time_start = j.data.time.epoch
        w.last_update = j.data.time.epoch
        w = self.model_worker.set(w)
        self.logger.debug("worker add")
        if onetime:
            myworker(w.id,onetime=onetime)
        else:
            worker = gipc.start_process(target=myworker,args=(w.id,))
            self.workers[w.id] = worker

    def _data_process(self,onetime=False):
        while True:
            #PROCESS DATA COMING BACK FROM WORKERS
            #needs to happen like this because we cant operate sqlite index from 2 location
            #because of this we also know data is never processed (written) elsewhere
            d = self.queue_data.get_nowait()
            while d != None:
                # print(self.queue_data.qsize())
                cat, id, data = j.data.serializers.msgpack.loads(d)
                if cat=="W":
                    #means is worker object
                    worker=self.model_worker.schema.get(capnpbin=data)
                    worker.id = id
                    self.model_worker.set(worker)
                    # self.logger.debug(worker)
                elif cat=="J":
                    #means is job object
                    job=self.model_job.schema.get(capnpbin=data)
                    job.id = id
                    self.model_job.set(job)
                    self.logger.debug(job)
                else:
                    raise RuntimeError("could not process returning data")
                d = self.queue_data.get_nowait()

            gevent.sleep(0.1) #important to not overload gedis
            if onetime:
                return


    def _main_loop(self,onetime=False):

        self.logger.debug("monitor start")

        def test_workers_more():
            nr_workers = self.nr_workers
            a = nr_workers < self.workers_nr_max
            b = nr_workers < self.queue.qsize() or nr_workers < self.workers_nr_min
            return a and b

        def test_workers_less():
            nr_workers = self.nr_workers
            a = nr_workers > self.workers_nr_max
            b = nr_workers > self.queue.qsize() and nr_workers > self.workers_nr_min
            return a or b

        while True:

            self.logger.debug("monitor run")

            #there is already 1 working, lets give 2 sec time before we start monitoring
            time.sleep(2)

            #test if we need to add workers
            while test_workers_more():
                print("WORKERS START")
                self._worker_start()

            #TEST for timeout
            from pudb import set_trace; set_trace()

            for wid, gproc in self.workers.items():
                if gproc.exitcode !=None:
                    raise RuntimeError("subprocess should never have been exitted")
                w = self.model_worker.get(wid)
                if w == None:
                    #should always find the worker
                    # j.shell()
                    continue

                job_running = w.current_job != 4294967295

                if job_running:
                    job = self.model_job.get(w.current_job)

                    if job.state != "OK" and j.data.time.epoch>job.time_start+job.timeout:
                        #WE ARE IN TIMEOUT
                        # print("TIMEOUT")
                        # print(w)
                        self.logger.info("KILL:%s in worker %s"%(w.id,job.id))
                        gproc.kill()
                        job.state = "ERROR"
                        job.error = "TIMEOUT"
                        job.time_stop = j.data.time.epoch
                        self.model_job.set(job)
                        print(job)
                        # restart worker
                        self.workers[w.id] = gipc.start_process(target = self._worker,args=(w.id,))

            #test if we have too many workers
            removed_one = False
            active_workers = [key for key in self.workers.keys()]
            active_workers.sort()
            for wid in active_workers:
                gproc = self.workers[wid]
                if gproc.exitcode != None:
                    raise RuntimeError("subprocess should never have been exitted")
                w = self.model_worker.get(wid)
                if w ==None:
                    j.shell()

                job_running = w.current_job != 4294967295
                self.logger.debug("job running:%s (%s)"%(job.id,job_running))

                if w.halt==False and not job_running and self.queue.qsize()==0:
                    if removed_one == False and test_workers_less():
                        self.logger.debug("worker remove:%s"%wid)
                        removed_one = True
                        w.halt = True
                        self.model_worker.set(w) #mark worker to halt
                        gproc.kill()
                        self.model_worker.delete(wid)
                        todel.append(wid)

            for item in todel:
                self.workers.pop(item)

            print(self.workers)

            self.logger.debug("nr workers:%s, queuesize:%s"%(self.nr_workers,self.queue.qsize()))

            if onetime:
                return


    def schedule(self,method,*args,category="", timeout=120, inprocess=False, **kwargs):
        self.init()
        code = inspect.getsource(method)
        code = j.core.text.strip(code)
        code = code.replace("self,","").replace("self ,","").replace("self  ,","")

        methodname = ''
        for line in code.split("\n"):
            if line.startswith("def "):
                methodname = line.split("(", 1)[0].strip().replace("def ","")

        if methodname == '':
            raise RuntimeError("defname cannot be empty")

        key = j.data.hash.md5_string(code)
        new, action = self.action_get(key)
        if new:
            action.code = code
            action.key = key
            action.methodname = methodname
            self.model_action.set(action)

        job = self.model_job.new()
        job.action_id = action.id
        job.time_start = j.data.time.epoch
        job.state = "NEW"
        job.timeout = timeout
        job.category = category
        job.args = j.data.serializers.json.dumps(args)
        job.kwargs = j.data.serializers.json.dumps(kwargs)
        job = self.model_job.set(job)

        if inprocess:
            j.shell()
        else:
            self.queue.put(job.id)
        return job.id

    def halt(self,graceful=True,reset=True):
        self.init()

        for wid, gproc in self.workers.items():
            if gproc.exitcode != None:
                raise RuntimeError("subprocess should never have been exitted")

            w = self.model_worker.get(wid)

            job_running = w.current_job != 4294967295

            if not graceful or not job_running:
                gproc.kill()

        if reset:
            self.model_action.destroy()
            self.model_job.destroy()
            self.model_worker.destroy()
            #delete the queue
            while self.queue.get_nowait() != None:
                pass



    def test(self):
        """
        js_shell "j.servers.myjobs.test()"
        :return:
        """
        self.init(reset=True)

        def add(a,b):
            return a+b


        def add_error(a,b):
            raise RuntimeError("s")

        def wait():
            import time
            time.sleep(10000)

        def wait_2sec():
            import time
            time.sleep(2)

        for x in range(10):
            self.schedule(add,1,2)

        j.servers.myjobs.schedule(add_error, 1, 2)

        self.schedule(wait, timeout=1)

        jobs = self.model_job.get_all()

        assert len(jobs) == 12

        self.start()

        time.sleep(3)
        #now timeout should have happened

        jobs = self.model_job.get_all()

        assert len(jobs) == 12

        errors = [job for job in jobs if job.error != ""]
        assert len(errors) == 2

        errors = [job for job in jobs if job.state == "ERROR"]
        assert len(errors) == 2

        errors = [job for job in jobs if job.error == "s"]
        assert len(errors) == 1

        errors = [job for job in jobs if job.error == "TIMEOUT"]
        assert len(errors) == 1

        jobs = [job for job in jobs if job.state == "OK"]
        assert len(jobs) == 10
        assert jobs[0].result == "3"

        for x in range(50):
            self.schedule(wait_2sec)


        while len(self.model_worker.get_all())>1:
            time.sleep(1)

        j.shell()

        print ("TEST OK")



        self.halt(reset=True)


    def test2(self):
        """
        js_shell "j.servers.myjobs.test2()"
        :return:
        """
        self.init(reset=True)


        def wait_2sec():
            import time
            time.sleep(2)

        for x in range(40):
            self.schedule(wait_2sec)

        self.start()

        gevent.joinall([self.dataloop, self.mainloop])


        print ("TEST OK")



        self.halt(reset=True)