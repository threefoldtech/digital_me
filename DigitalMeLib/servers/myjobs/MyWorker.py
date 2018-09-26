




def myworker(id=999999,onetime=False,showout=False):
    """
    js_shell "j.servers.myjobs.worker()"
    :return:
    """

    from Jumpscale import j

    j.clients.redis.cache_clear()  # make sure we have redis connections empty, because comes from parent

    redisdb = j.clients.redis.core_get()

    queue = j.clients.redis.getQueue(redisclient=redisdb, name="myjobs", fromcache=False)
    queue_data = j.clients.redis.getQueue(redisclient=redisdb, name="myjobs_datachanges", fromcache=False)

    def return_data(cat, obj):
        data = j.data.serializers.msgpack.dumps([cat, obj.id, obj._data])
        queue_data.put(data)

    def return_job_obj(obj):
        return_data("J", obj)

    def return_worker_obj(obj):
        return_data("W", obj)


    bcdb = j.data.bcdb.bcdb_instances["myjobs"]
    model_job = bcdb.models["jumpscale.myjobs.job"]
    model_action = bcdb.models["jumpscale.myjobs.action"]
    model_worker = bcdb.models["jumpscale.myjobs.worker"]

    w = model_worker.get(id)
    while w==None:
        time.sleep(0.1)
        print(3)
        w = model_worker.get(id)

    w.current_job = 4294967295  # means nil
    w.halt = False
    w.running = True
    return_worker_obj(w)

    while True:
        res = queue.get(timeout=10)
        if res == None:
            if showout:
                print("queue request timeout, continue")
            w = model_worker.get(id)
            #have to fetch this again because was waiting on queue
            if w == None:
                # raise RuntimeError("worker should always be there")
                return
            w.current_job = 4294967295  # means nil
            return_worker_obj(w)
            if w.halt:
                # model_worker.
                print("WORKER REMOVE SELF:%s" % id)
                return
        else:
            res.decode()
            jobid = int(res)
            # update worker has been active
            w = model_worker.get(id)
            if w == None:
                #means worker no longer in db
                print("WORKER REMOVE SELF:%s" % id)
                return
            if res == "halt":
                return
            w.last_update = j.data.time.epoch
            w.current_job = jobid
            return_worker_obj(w)
            job = model_job.get(id=jobid)
            if job == None:
                print("ERROR: job:%s not found"%jobid)
            else:
                #now have job
                action = model_action.get(job.action_id)
                if action == None:
                    raise RuntimeError("ERROR: action:%s not found"%job.action_id)
                kwargs = j.data.serializers.json.loads(job.kwargs)
                args = j.data.serializers.json.loads(job.args)

                w.last_update = j.data.time.epoch
                w.current_job = jobid #set current jobid
                return_worker_obj(w)

                if showout:
                    print("EXECUTE")
                    print(job)

                try:
                    exec(action.code)
                    method = eval(action.methodname)
                except Exception as e:
                    job.error = str(e)+"\nCOULD NOT GET TO METHOD, IMPORT ERROR."
                    job.state = "ERROR"
                    job.time_stop = j.data.time.epoch
                    return_job_obj(job)
                    if showout:
                        print("ERROR:%s"%e)
                    if onetime:
                        return
                    continue

                try:
                   res  = method(*args,**kwargs)
                except Exception as e:
                    job.error = str(e)
                    job.state = "ERROR"
                    job.time_stop = j.data.time.epoch
                    return_job_obj(job)
                    if showout:
                        print("ERROR:%s"%e)
                    if onetime:
                        return
                    continue

                try:
                    job.result = j.data.serializers.json.dumps(res)
                except Exception as e:
                    job.error = str(e)+"\nCOULD NOT SERIALIZE RESULT OF THE METHOD, make sure json can be used on result"
                    job.state = "ERROR"
                    job.time_stop = j.data.time.epoch
                    return_job_obj(job)
                    if showout:
                        print("ERROR:%s"%e)
                    if onetime:
                        return
                    continue

                job.time_stop = j.data.time.epoch
                job.state = "OK"

                if showout:
                    print("OK")
                    print(job)

                return_job_obj(job)

                w.current_job = 4294967295
                return_worker_obj(w)

        if onetime:
            return