from Jumpscale import j

JSBASE = j.application.JSBaseClass


class system(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.server = j.servers.gedis.latest

    def ping(self):
        return "PONG"

    def auth(self, secret, namespace=""):
        secret = secret.decode()
        # check admin secret
        if self.server.config.data["adminsecret_"] == secret:
            return "OK"

        j.shell()
        return "AUTHERROR"

    def ping_bool(self):
        return True

    def core_schemas_get(self, namespace):
        """
        return all core schemas as understood by the server, is as text, can be processed by j.data.schema

        """
        namespace = namespace.decode()
        res = {}
        for key, item in j.data.schema.schemas.items():
            # TODO: should prob limit to namespace
            res[key] = item.text
        return j.data.serializers.msgpack.dumps(res)

    def api_meta(self, namespace):
        """
        return the api meta information

        """
        namespace = namespace.decode()
        res = {}
        res["cmds"] = {}
        for key, item in self.server.cmds_meta.items():
            if item.namespace == namespace:
                res["cmds"][key] = item.data._data
        return j.data.serializers.msgpack.dumps(res)

    def schema_urls(self, *args):
        """
        return the api meta information

        """
        s = self.server.schema_urls
        return j.data.serializers.msgpack.dumps(s)

    def filemonitor_paths(self, schema_out):
        """
        return all paths which should be monitored for file changes
        ```out
        paths = (LS)
        ```
        """

        r = schema_out.new()

        # monitor changes for the docsites (markdown)
        for key, item in j.tools.docsites.docsites.items():
            r.paths.append(item.path)

        # monitor change for the webserver  (schema's are in there)
        r.paths.append(j.servers.web.latest.path)

        # changes for the actors
        r.paths.append(j.servers.gedis.latest.code_generated_dir)
        r.paths.append(j.servers.gedis.latest.app_dir + "/actors")
        r.paths.append("%s/systemactors" % j.servers.gedis.path)

        return r

    def filemonitor_event(self, changeobj):
        """
        used by filemonitor daemon to escalate events which happened on filesystem

        ```in
        src_path = (S)
        event_type = (S)
        is_directory = (B)
        ```

        """

        # Check if a blueprint is changed
        # if changeobj.is_directory:
        #     path_parts = changeobj.src_path.split('/')
        #     if path_parts[-2] == 'blueprints':
        #         blueprint_name = "{}_blueprint".format(path_parts[-1])
        #         bp = j.servers.web.latest.app.app.blueprints.get(blueprint_name)
        #         if bp:
        #             self.logger.info("reloading blueprint : {}".format(blueprint_name))
        #             del (j.servers.web.latest.app.app.blueprints[blueprint_name])
        #             j.servers.web.latest.app.app.register_blueself.logger.info(bp)
        #             return

        # Check if docsite is changed
        if changeobj.is_directory:
            docsites = j.tools.docsites.docsites
            for _, docsite in docsites.items():
                if docsite.path in changeobj.src_path:
                    docsite.load()
                    self.logger.info("reloading docsite: {}".format(docsite))
                    return

        # check if path is actor if yes, reload that one
        if not changeobj.is_directory and changeobj.src_path.endswith('.py'):
            paths = list()
            paths.append(j.servers.gedis.latest.code_generated_dir)
            paths.append(j.servers.gedis.latest.app_dir + "/actors")
            paths.append("%s/systemactors" % j.servers.gedis.path)
            # now check if path is in docsites, if yes then reload that docsite only !
            for path in paths:
                if path in changeobj.src_path:
                    actor_name = j.sal.fs.getBaseName(changeobj.src_path)[:-3].lower()
                    namespace = j.servers.gedis.latest.instance + '.' + actor_name
                    if namespace in j.servers.gedis.latest.cmds_meta:
                        del (j.servers.gedis.latest.cmds_meta[namespace])
                        del (j.servers.gedis.latest.classes[namespace])
                        for cmd in list(j.servers.gedis.latest.cmds.keys()):
                            if actor_name in cmd:
                                del (j.servers.gedis.latest.cmds[cmd])
                        j.servers.gedis.latest.cmds_add(namespace, path=changeobj.src_path)
                        self.logger.info("reloading namespace: {}".format(namespace))
                        return

        return

    # def test(self,name,nr,schema_out):
    #     """
    #     some test method, which returns something easy
    #
    #     ```in
    #     name = ""
    #     nr = 0 (I)
    #     ```
    #
    #     ```out
    #     name = ""
    #     nr = 0 (I)
    #     list_int = (LI)
    #     ```
    #
    #     """
    #     o=schema_out.new()
    #     o.name = name
    #     o.nr = nr
    #     # o.list_int = [1,2,3]
    #
    #     return o
    #
    # def test_nontyped(self,name,nr):
    #     return [name,nr]

    def get_web_client(self):
        return j.servers.gedis.latest.web_client_code

    def _options(self, args, nr_args=1):
        res = []
        res2 = {}
        key = ""
        nr = 0
        for arg in args:
            nr += 1
            if nr < nr_args + 1:
                val = args[nr - 1].decode()
                res.append(val)
                continue
            else:
                if key == "":
                    key = args[nr - 1].decode()
                    if not j.data.types.string.check(key):
                        raise RuntimeError("%s: key:%s need to be string" % (args, key))
                else:
                    res2[key] = args[nr - 1].decode()
                    key = ""
        return res, res2

    def scan(self, *args):
        args, kwargs = self._options(args, 1)
        # match = kwargs.get("MATCH","*")
        # maxcount = int(kwargs.get("COUNT", "0"))
        res = ["*REDIS*", "0"]
        res2 = []
        # nr=0
        g = j.servers.gedis.latest
        for namespace in g.namespaces:
            res2.append("NAMESPACES:%s" % namespace)
        res.append(res2)
        return res

    def type(self, *args):
        return "string"

    def ttl(self, *args):
        return -1

    def get(self, *args):
        g = j.servers.gedis.latest
        key = args[0].decode()
        splitted = key.split(":")
        if len(splitted) == 2:
            cmd = splitted[0].lower()
            val = splitted[1]

            if cmd == 'namespaces':
                actors = g.actors_methods_list(namespace=val)
                return j.data.serializers.json.dumps(actors).encode()

            return str(g.cmds_meta)

        j.shell()
        w
        return b"THIS IS A TEST"

    def hlen(self, *args):
        return 10

    def info(self, *args):
        C = """
        # Server
        redis_version:999.999.999
        redis_git_sha1:3c968ff0
        redis_git_dirty:0
        redis_build_id:51089de051945df4
        redis_mode:standalone
        os:Linux 4.8.0-1-amd64 x86_64
        arch_bits:64
        multiplexing_api:epoll
        atomicvar_api:atomic-builtin
        gcc_version:6.3.0
        process_id:25508
        run_id:39240fffc9d38736f9b96bdf6f7d942232fddef0
        tcp_port:6379
        uptime_in_seconds:2745349
        uptime_in_days:31
        hz:10
        lru_clock:10789633
        executable:/usr/local/bin/redis-server
        config_file:

        # Clients
        connected_clients:4
        client_longest_output_list:0
        client_biggest_input_buf:0
        blocked_clients:0

        # Memory
        used_memory:266093896
        used_memory_human:253.77M
        used_memory_rss:275234816
        used_memory_rss_human:262.48M
        used_memory_peak:266122152
        used_memory_peak_human:253.79M
        used_memory_peak_perc:99.99%
        used_memory_overhead:79271080
        used_memory_startup:510704
        used_memory_dataset:186822816
        used_memory_dataset_perc:70.34%
        allocator_allocated:266075864
        allocator_active:266338304
        allocator_resident:274309120
        total_system_memory:1044770816
        total_system_memory_human:996.37M
        used_memory_lua:37888
        used_memory_lua_human:37.00K
        maxmemory:0
        maxmemory_human:0B
        maxmemory_policy:noeviction
        allocator_frag_ratio:1.00
        allocator_frag_bytes:262440
        allocator_rss_ratio:1.03
        allocator_rss_bytes:7970816
        rss_overhead_ratio:1.00
        rss_overhead_bytes:925696
        mem_fragmentation_ratio:1.03
        mem_fragmentation_bytes:9223928
        mem_allocator:jemalloc-4.0.3
        active_defrag_running:0
        lazyfree_pending_objects:0

        # Persistence
        loading:0
        rdb_changes_since_last_save:7542528
        rdb_bgsave_in_progress:0
        rdb_last_save_time:1534770940
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
        total_connections_received:24
        total_commands_processed:18574246
        instantaneous_ops_per_sec:4
        total_net_input_bytes:1532181242
        total_net_output_bytes:259667683
        instantaneous_input_kbps:0.37
        instantaneous_output_kbps:0.05
        rejected_connections:0
        sync_full:0
        sync_partial_ok:0
        sync_partial_err:0
        expired_keys:24320
        expired_stale_perc:0.00
        expired_time_cap_reached_count:0
        evicted_keys:0
        keyspace_hits:4308238
        keyspace_misses:1813568
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
        master_replid:e06cc8078080966de939fa81fa64259a5bd9408f
        master_replid2:0000000000000000000000000000000000000000
        master_repl_offset:0
        second_repl_offset:-1
        repl_backlog_active:0
        repl_backlog_size:1048576
        repl_backlog_first_byte_offset:0
        repl_backlog_histlen:0

        # CPU
        used_cpu_sys:2148.25
        used_cpu_user:16114.97
        used_cpu_sys_children:0.00
        used_cpu_user_children:0.00

        # Cluster
        cluster_enabled:0

        # Keyspace
        db0:keys=1545562,expires=805,avg_ttl=59291968309110
        """
        return j.core.text.strip(C)
