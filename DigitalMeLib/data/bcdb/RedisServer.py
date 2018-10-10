from Jumpscale import j
import json
from gevent.pool import Pool
from gevent import time,signal
import gevent
from gevent.server import StreamServer
from redis.exceptions import ConnectionError
from DigitalMeLib.servers.gedis.protocol import RedisResponseWriter, RedisCommandParser

JSBASE = j.application.JSBaseClass


class RedisServer(JSBASE):
    def __init__(self, bcdb):
        JSBASE.__init__(self)
        self.bcdb = bcdb
        self._sig_handler = []
        self.logger_enable()
        self.host = "localhost"
        self.port = 6380  #1 port higher than the std port
        self.ssl = False

    def init(self):
        self._sig_handler.append(gevent.signal(signal.SIGINT, self.stop))
        if self.ssl:
            self.ssl_priv_key_path, self.ssl_cert_path = self.sslkeys_generate()
            # Server always supports SSL
            # client can use to talk to it in SSL or not
            self.redis_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=self.handle_redis,
                keyfile=self.ssl_priv_key_path,
                certfile=self.ssl_cert_path
            )
        else:
            self.redis_server = StreamServer(
                (self.host, self.port),
                spawn=Pool(),
                handle=self.handle_redis
            )

    def start(self):
        print("RUNNING")
        print(self)
        self.redis_server.serve_forever()

    def stop(self):
        """
        stop receiving requests and close the server
        """
        # prevent the signal handler to be called again if
        # more signal are received
        for h in self._sig_handler:
            h.cancel()

        self.logger.info('stopping server')
        self.redis_server.stop()



    def handle_redis(self, socket, address):

        parser = RedisCommandParser(socket)
        response = RedisResponseWriter(socket)

        try:
            self._handle_redis(socket, address, parser, response)
        except ConnectionError as err:
            self.logger.info('connection error: {}'.format(str(err)))
        finally:
            parser.on_disconnect()
            self.logger.info('close connection from {}'.format(address))

    def _handle_redis(self, socket, address, parser, response):

        self.logger.info('connection from {}'.format(address))
        socket.namespace = "system"

        while True:
            request = parser.read_request()

            self.logger.debug("%s:%s"%(socket.namespace,request))

            if request is None:
                self.logger.debug("connection lost or tcp test")
                break

            if not request:  # empty list request
                # self.response.error('Empty request body .. probably this is a (TCP port) checking query')
                self.logger.debug("EMPTYLIST")
                continue

            cmd = request[0]
            redis_cmd = cmd.decode("utf-8").lower()


            if redis_cmd == "command":
                response.encode("OK")
                continue

            elif redis_cmd == "ping":
                response.encode("PONG")
                continue

            elif redis_cmd == "info":
                self.info_internal(response)
                continue

            elif redis_cmd == "select":
                if request[1] == b'0':
                    response.encode("OK")
                    continue
                response.error("DB index is out of range")
                continue

            elif redis_cmd == "set":
                self.set(response, request[1].decode(), request[2].decode())
                continue
            elif redis_cmd in ["hscan"]:
                kwargs = parser.request_to_dict(request[3:])
                if not hasattr(self, redis_cmd):
                    raise  RuntimeError("COULD NOT FIND COMMAND:%s"%redis_cmd)
                    response.error("COULD NOT FIND COMMAND:%s"%redis_cmd)
                else:
                    method = getattr(self, redis_cmd)
                    start_obj = int(request[2].decode())
                    key = request[1].decode()
                    method(response,key, start_obj,**kwargs)
                continue

            else:
                print(request)
                kwargs = parser.request_to_dict(request)
                arg = kwargs.pop(redis_cmd)
                if redis_cmd=="del":
                    redis_cmd="delete"
                if not hasattr(self, redis_cmd):
                    # raise  RuntimeError("COULD NOT FIND COMMAND:%s"%redis_cmd)
                    j.shell()
                    response.error("COULD NOT FIND COMMAND:%s"%redis_cmd)
                else:
                    method = getattr(self, redis_cmd)
                    method(response,arg,**kwargs)
                continue


    def info(self):
        return b"NO INFO YET"

    def _split(self,key):
        splitted=key.split(":")
        m = ""
        if len(splitted) == 1:
            cat=splitted[0]
            url = ""
            key = ""
        elif len(splitted)==2:
            cat=splitted[0]
            url = splitted[1]
            key = ""
        elif len(splitted)==2:
            cat=splitted[0]
            url = splitted[1]
            key = splitted[2]
        if url != "":
            if url in self.bcdb.models:
                m = self.bcdb.model_get(url)

        return (cat,url,key,m)

    def delete(self, response, key):
        cat, url, key, model = self._split(key)
        if url == "":
            response.encode("0")
            return
        if cat=="schemas":
            response.encode("0")
            return
        elif cat == "objects":
            if key=="":
                #remove all items from model
                j.shell()
            else:
                #remove 1 item from model
                j.shell()

        else:
            response.error("cannot delete, cat:'%s' not found"%cat)

    def hlen(self, response, key):
        cat, url, key, model = self._split(key)
        j.shell()

    def get(self, response, key):
        cat, url, key, model = self._split(key)
        if url == "":
            response.encode("ok")
            return
        if cat == "info":
            response.encode(self.info())
            return
        elif cat == "schemas":
            if url == "":
                response.encode("")
                return
            elif key == "":
                response.encode(m.schema.text)
                return
        else:
            j.shell()

    def hget(self, response, key):
        cat, url, key, model = self._split(key)
        if url == "":
            response.encode("ok")
            return
        elif cat == "objects":
            j.shell()
            o=model.get(int(id))
            response.encode(o._json)
            return
        else:
            j.shell()


    def set(self,response,key,val):
        cat, url, key, model = self._split(key)
        if url == "":
            response.error("url needs to be known, otherwise cannot set e.g. objects:despiegk.test:new")
        if key == "":
            response.error("key needs to be known, e.g. objects:despiegk.test:new or in stead of new e.g. 101 (id)")

        if cat == "schemas":
            s = j.data.schema.add(schema=val)
            self.bcdb.model_add_from_schema(schema_url=s.url)
            response.encode("OK")
            return
        else:
            j.shell()

    def hset(self,response,key,val):
        cat, url, key, model = self._split(key)
        if url == "":
            response.error("url needs to be known, otherwise cannot set e.g. objects:despiegk.test:new")
        if key == "":
            response.error("key needs to be known, e.g. objects:despiegk.test:new or in stead of new e.g. 101 (id)")

        if cat == "objects":
            j.shell()
            if id=="new":
                o=m.set_dynamic(val)
            else:
                id=int(key)
                o = m.set_dynamic(val,obj_id=id)
            response.encode("%s"%o.id)
            return
        else:
            j.shell()

    def ttl(self,response,key):
        response.encode("-1")

    def type(self,response,type):
        """
        :param type: is the key we need to give type for
        :return:
        """
        cat, url, key, model = self._split(type)
        if key=="" and url!="":
            #then its hset
            response.encode("hash")
        else:
            response.encode("string")

    def _urls(self):
        urls = [i for i in self.bcdb.models.keys()]
        return urls

    def hscan(self,response,key,startid,count=10000):
        res = []
        response._array(["0", res])

    def scan(self,response,startid,match='*',count=10000):
        """

        :param scan: id to start from
        :param match: default *
        :param count: nr of items per page
        :return:
        """
        #in first version will only do 1 page, so ignore scan
        res=[]

        if len(self.bcdb.models)>0:
            for url,model in self.bcdb.models.items():
                res.append("schemas:%s"%url)
                res.append("objects:%s" % url)
        else:
            res.append("schemas")
            res.append("objects")
        res.append("info")
        response._array(["0",res])


    def info_internal(self,response):
        C="""
        # Server
        redis_version:4.0.11
        redis_git_sha1:00000000
        redis_git_dirty:0
        redis_build_id:13f90e3a88f770eb
        redis_mode:standalone
        os:Darwin 17.7.0 x86_64
        arch_bits:64
        multiplexing_api:kqueue
        atomicvar_api:atomic-builtin
        gcc_version:4.2.1
        process_id:93263
        run_id:49afb34b519a889778562b7addb5723c8c45bec4
        tcp_port:6380
        uptime_in_seconds:3600
        uptime_in_days:1
        hz:10
        lru_clock:12104116
        executable:/Users/despiegk/redis-server
        config_file:
        
        # Clients
        connected_clients:1
        client_longest_output_list:0
        client_biggest_input_buf:0
        blocked_clients:52
        
        # Memory
        used_memory:11436720
        used_memory_human:10.91M
        used_memory_rss:10289152
        used_memory_rss_human:9.81M
        used_memory_peak:14691808
        used_memory_peak_human:14.01M
        used_memory_peak_perc:77.84%
        used_memory_overhead:2817866
        used_memory_startup:980704
        used_memory_dataset:8618854
        used_memory_dataset_perc:82.43%
        total_system_memory:17179869184
        total_system_memory_human:16.00G
        used_memory_lua:37888
        used_memory_lua_human:37.00K
        maxmemory:100000000
        maxmemory_human:95.37M
        maxmemory_policy:noeviction
        mem_fragmentation_ratio:0.90
        mem_allocator:libc
        active_defrag_running:0
        lazyfree_pending_objects:0
        
        # Persistence
        loading:0
        rdb_changes_since_last_save:66381
        rdb_bgsave_in_progress:0
        rdb_last_save_time:1538289882
        rdb_last_bgsave_status:ok
        rdb_last_bgsave_time_sec:-1
        rdb_current_bgsave_time_sec:-1
        rdb_last_cow_size:0
        aof_enabled:0
        aof_rewrite_in_progress:0
        aof_rewrite_scheduled:0
        aof_last_rewrite_time_sec:-1
        aof_current_rewrite_time_sec:-1
        aof_last_bgrewrite_status:ok
        aof_last_write_status:ok
        aof_last_cow_size:0
        
        # Stats
        total_connections_received:627
        total_commands_processed:249830
        instantaneous_ops_per_sec:0
        total_net_input_bytes:22576788
        total_net_output_bytes:19329324
        instantaneous_input_kbps:0.01
        instantaneous_output_kbps:6.20
        rejected_connections:2
        sync_full:0
        sync_partial_ok:0
        sync_partial_err:0
        expired_keys:5
        expired_stale_perc:0.00
        expired_time_cap_reached_count:0
        evicted_keys:0
        keyspace_hits:76302
        keyspace_misses:3061
        pubsub_channels:0
        pubsub_patterns:0
        latest_fork_usec:0
        migrate_cached_sockets:0
        slave_expires_tracked_keys:0
        active_defrag_hits:0
        active_defrag_misses:0
        active_defrag_key_hits:0
        active_defrag_key_misses:0
        
        # Replication
        role:master
        connected_slaves:0
        master_replid:49bcd83fa843f4e6657440b7035a1c2314766ac4
        master_replid2:0000000000000000000000000000000000000000
        master_repl_offset:0
        second_repl_offset:-1
        repl_backlog_active:0
        repl_backlog_size:1048576
        repl_backlog_first_byte_offset:0
        repl_backlog_histlen:0
        
        # CPU
        used_cpu_sys:101.39
        used_cpu_user:64.27
        used_cpu_sys_children:0.00
        used_cpu_user_children:0.00
        
        # Cluster
        cluster_enabled:0
        
        # Keyspace
        # db0:keys=10000,expires=1,avg_ttl=7801480
        """
        C=j.core.text.strip(C)
        response.encode(C)
