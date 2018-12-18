
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
return_queues = (LS)


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
        self.workers_subprocess = True
        self._logger_enable()

    def init(self,reset=False,start=True):
        """

        :param db_cl: if None will use db_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)
        :return:
        """
        if self._init == False or reset:

            if self.mainloop == None and  self.dataloop == None:
                from gevent import monkey
                monkey.patch_all()

            if self.mainloop != None:
                self.mainloop.kill()

            if self.dataloop != None:
                self.dataloop.kill()

            db = j.data.bcdb.get(j.core.db, namespace="myjobs", reset=reset,json_serialize=True)

            self.model_job = db.model_create(schema=schema_job)
            self.model_action = db.model_create(schema=schema_action)
            self.model_worker = db.model_create(schema=schema_worker)

            if reset:
                self.halt(reset=True)

            if start:
                self._start()

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

    def _start(self,onetime=False):
        """

        :param nr_max: max nr of workers which can be started
        :return:
        """
        if self.workers_subprocess:
            self._worker_start(onetime=onetime) #start first worker
        if onetime:
            self._data_process(onetime=True)
        else:
            self.dataloop = gevent.spawn(self._data_process)
            if self.workers_subprocess:
                self.mainloop = gevent.spawn(self._main_loop)


    def _worker_start(self,onetime=False):
        w = self.model_worker.new()
        w.time_start = j.data.time.epoch
        w.last_update = j.data.time.epoch
        w = self.model_worker.set(w)
        self._logger.debug("worker add")
        if onetime:
            myworker(w.id,onetime=onetime)
        else:
            worker = gipc.start_process(target=myworker,args=(w.id,))
            self.workers[w.id] = worker

    def worker_start_inprocess(self):
        """
        js_shell "j.servers.myjobs.worker_start_inprocess()"
        :return:
        """
        self.init(reset=False,start=False)
        w = self.model_worker.new()
        w.time_start = j.data.time.epoch
        w.last_update = j.data.time.epoch
        w = self.model_worker.set(w)
        self._logger.debug("worker started:%s"%w.id)
        myworker(w.id,showout=True)



    def _main_loop(self):

        self._logger.debug("monitor start")

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

            self._logger.debug("monitor run")

            # #there is already 1 working, lets give 2 sec time before we start monitoring
            # time.sleep(2)

            #TEST for timeout
            wids = [key for key in self.workers.keys()]
            for wid in wids:
                if wid in self.workers:
                    gproc = self.workers[wid]
                else:
                    continue
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

                    if job !=None and job.state != "OK" and j.data.time.epoch>job.time_start+job.timeout:
                        #WE ARE IN TIMEOUT
                        # print("TIMEOUT")
                        # print(w)
                        self._logger.info("KILL:%s in worker %s"%(w.id,job.id))
                        gproc.kill()
                        self.workers.pop(wid)
                        job.state = "ERROR"
                        job.error = "TIMEOUT"
                        job.time_stop = j.data.time.epoch
                        self.model_job.set(job)
                        print(job)
                        # make sure right nr of workers are active
                        self._worker_start()

            if test_workers_more():
                #test if we need to add workers
                while test_workers_more():
                    print("WORKERS START")
                    self._worker_start()
            else:

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
                        continue

                    job_running = w.current_job != 4294967295
                    self._logger.debug("job running:%s (%s)"%(w.id,job_running))

                    if w.halt==False and not job_running and self.queue.qsize()==0:
                        if removed_one == False and test_workers_less():
                            self._logger.debug("worker remove:%s"%wid)
                            removed_one = True
                            w.halt = True
                            self.model_worker.set(w) #mark worker to halt
                            gproc.kill()
                            gproc.terminate()
                            self.model_worker.delete(wid)
                            gproc2 = self.workers[wid]
                            while gproc.is_alive():
                                gevent.sleep(0.1)
                                print("worker,killing:%s"%wid)
                            assert gproc2.is_alive() == False
                            self.workers.pop(wid)

            # print(self.workers)

            self._logger.debug("nr workers:%s, queuesize:%s"%(self.nr_workers,self.queue.qsize()))
            gevent.sleep(1)



    def schedule(self,method,*args,category="", timeout=120, inprocess=False, return_queues=[],
                 return_queues_reset=False, gevent=False, **kwargs):
        """

        :param method:
        :param args:
        :param category:
        :param timeout:
        :param inprocess:
        :param return_queues: the result job id will be posted on the specified return_queue names (error or ok)
        :param return_queues_reset, if True will make sure the queues are empty
        :param gevent: means return queues will not be kept in redis, but in gevent queues
        :param kwargs:
        :return:
        """
        if inprocess:
            return method(*args,**kwargs)
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
        if not gevent:
            for qname in return_queues:
                job.return_queues.append(qname)
                if return_queues_reset:
                    q = j.clients.redis.getQueue(redisclient=j.clients.redis.core_get(), name="myjobs:%s" % queue_name)
                    q.reset()
        job = self.model_job.set(job)

        if gevent and return_queues != []:
            # self.return_queues[job.id]
            raise RuntimeError("need to implement")

        self.queue.put(job.id)

        return job.id

    def result_queue_get(self,queue_name,timeout=10,nr_items=1):
        """
        wait for job to return on queue
        :param queue_name:
        :param timeout:
        :param nr_items: will only return when nr of items equal min set, if more than 1 then as list
        :return:
        """
        res=[]
        if nr_items>1:
            while True:
                job = self.result_queue_get(queue_name=queue_name, timeout=timeout)
                res.append(job)
                if len(res)+1>nr_items:
                    return res
        else:
            job = self.result_queue_get( queue_name=queue_name, timeout=timeout)
        return job

    def _result_queue_get(self,queue_name,timeout=10):
        """
        will wait for 1 entry to come in queue & will return it
        :param queue_name:
        :param timeout:
        :return:
        """
        q=j.clients.redis.getQueue(redisclient=j.clients.redis.core_get(), name="myjobs:%s" % queue_name)
        data = q.get(timeout=timeout)
        if data is None:
            raise RuntimeError("timeout on wait for queue:%s"%queue_name)
        jid,data_ret=j.data.serializers.msgpack.loads(data)
        j.shell()
        w
        job = self.model_job.schema.get(capnpbin=data_ret)
        job.id = jid
        return job

    def halt(self,graceful=True,reset=True):

        if self.mainloop != None:
            self.mainloop.kill()

        if self.dataloop != None:
            self.dataloop.kill()

        for wid, gproc in self.workers.items():
            if gproc.exitcode != None:
                continue

            w = self.model_worker.get(wid)

            job_running = w.current_job != 4294967295

            if not graceful or not job_running:
                gproc.kill()
                gproc.terminate() #dont know difference

        if reset:
            self.model_action.destroy()
            self.model_job.destroy()
            self.model_worker.destroy()
            #delete the queue
            while self.queue.get_nowait() != None:
                pass

    def results(self,ids,timeout=10):
        res = {}
        counter=0
        while len(ids)>0:
            id=ids[0]
            job = self.model_job.get(id)
            if job == None:
                raise RuntimeError("job:%s not found"%id)
            if job.time_stop!=0:
                if job.state=="OK":
                    res[id] = job.result
                    ids=ids[1:]
                else:
                    raise RuntimeError("job in eror:\n%s"%job)
            if len(ids) > 0:
                gevent.sleep(0.1)
                counter+=1
                if counter>timeout*10:
                    raise RuntimeError("timeout for results with jobids:%s"%ids)
        return res


    def test(self):
        """
        js_shell "j.servers.myjobs.test()"
        :return:
        """
        self.test1()
        self.test2()
        self.test3()
        print("TEST MYWORKERS FOR 3 TESTS DONE")


    def test1(self):
        """
        js_shell "j.servers.myjobs.test1()"
        :return:
        """

        def kill():
            #kill leftovers from last time, if any
            session = j.tools.tmux.session_get('main')
            session.window_remove("myworker_worker")
            self.init(reset=True,start=False)
            jobs = self.model_job.get_all()
            assert len(jobs)==0
            assert self.queue.qsize() == 0
            self.workers_subprocess = True

        kill()

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




        #test the behaviour for 1 job in process, only gevent for data handling
        j.servers.myjobs.schedule(add_error, 1, 2)
        self._start(onetime=True)

        jobs = self.model_job.get_all()
        assert len(jobs) == 1
        job = jobs[0]
        assert job.error == "s"
        assert job.id == 0
        assert job.result == ""
        assert job.state == "ERROR"
        assert job.time_stop >0

        j.servers.myjobs.schedule(add, 1, 2)
        self._start(onetime=True)

        jobs = self.model_job.get_all()
        assert len(jobs) == 2
        job = jobs[1]
        assert job.error == ""
        assert job.id == 1
        assert job.result == '3'
        assert job.state == "OK"
        assert job.time_stop >0

        res = self.results([1])

        assert res == {1: '3'}  #is the result back

        assert 3==j.servers.myjobs.schedule(add, 1, 2,inprocess=True)

        #lets start from scratch, now we know the super basic stuff is working

        self.workers_subprocess = False #will test with independent worker in tmux

        self.init(reset=True)

        for x in range(10):
            self.schedule(add,1,2)

        j.servers.myjobs.schedule(add_error, 1, 2)

        jobs = self.model_job.get_all()

        assert len(jobs) == 11

        assert self.queue.qsize() == 11 #there need to be 12 jobs in queue

        def tmuxexec():
            #lets now run the job executor in tmux, see it runs well in process
            cmd = 'js_shell "j.servers.myjobs.worker_start_inprocess()"'
            j.tools.tmux.execute(
                cmd,
                session='main',
                window='myworker_worker',
                pane='main',
                session_reset=False,
                window_reset=True
            )

            time.sleep(1)
            assert self.queue.qsize() == 0

        tmuxexec()

        print("WORKER STARTED IN TMUX")

        print("will wait for results")
        assert self.results([1, 2, 3],timeout=1) == {1: '3', 2: '3', 3: '3'}

        jobs = self.model_job.get_all()
        errors = [job for job in jobs if job.state == "ERROR"]
        assert len(errors) == 1

        #test with publish_subscribe channels
        queue_name="myself"
        q=j.clients.redis.getQueue(redisclient=j.clients.redis.core_get(), name="myjobs:%s" % queue_name)
        q.reset() #lets make sure its empty

        j.servers.myjobs.schedule(add,1,2,return_queues=[queue_name])
        time.sleep(0.5)
        assert q.qsize() == 1
        job_return = j.servers.myjobs.wait("myself")
        assert job_return.result == '3'
        assert job_return.id == 11
        assert job_return.state == 'OK'

        kill()

        #TMUX and in process tests are done, lets now see if as subprocess it works

        self.init(reset=True,start=True)

        print("wait to schedule jobs")
        gevent.sleep(2)





        for x in range(20):
            self.schedule(wait_2sec)

        j.servers.myjobs.schedule(wait,timeout=1)
        j.servers.myjobs.schedule(add_error, 1, 2)

        print("there should be 10 workers, so wait is max 5 sec")
        gevent.sleep(5)

        #now timeout should have happened & all should have executed

        jobs = self.model_job.get_all()
        assert len(jobs) == 22

        completed = [job for job in jobs if job.time_stop !=0]

        assert len(completed)==22


        errors = [job for job in jobs if job.error != ""]
        assert len(errors) == 2

        errors = [job for job in jobs if job.state == "ERROR"]
        assert len(errors) == 2

        errors = [job for job in jobs if job.error == "s"]
        assert len(errors) == 1

        errors = [job for job in jobs if job.error == "TIMEOUT"]
        assert len(errors) == 1

        jobs = [job for job in jobs if job.state == "OK"]
        assert len(jobs) == 20

        self.halt(reset=True)

        print ("TEST1 OK, ALL PASSED")



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

    def test3(self):
        """
        js_shell "j.servers.myjobs.test3()"
        :return:
        """
        self.init(reset=True)
        self.workers_nr_max= 100

        def wait_1sec():
            import time
            time.sleep(1)
            return "OK"

        ids=[]
        for x in range(100):
            ids.append(self.schedule(wait_1sec))

        res = self.results(ids)

        j.shell()

    def test4(self):
        """
        js_shell "j.servers.myjobs.test2()"
        :return:
        """

        def use_jumpscale():
            return j.data.serializers.json.dumps([1,2])

        self.result_queue_get()
