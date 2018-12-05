from Jumpscale import j
from redis.exceptions import ConnectionError

from .protocol import RedisCommandParser, RedisResponseWriter

JSBASE = j.application.JSBaseClass


class Handler(JSBASE):
    def __init__(self, gedis_server):
        JSBASE.__init__(self)
        self.gedis_server = gedis_server
        self.cmds = {}  # caching of commands
        self.classes = self.gedis_server.classes
        self.cmds_meta = self.gedis_server.cmds_meta
        self.logger_enable()

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
            self.logger.debug("%s:%s" % (socket.namespace, request))

            if request is None:
                self.logger.debug("connection lost or tcp test")
                break

            if not request:  # empty list request
                # self.response.error('Empty request body .. probably this is a (TCP port) checking query')
                self.logger.debug("EMPTYLIST")
                continue

            cmd = request[0]
            redis_cmd = cmd.decode("utf-8").lower()

            # special command to put the client on right namespace
            if redis_cmd == "select":
                namespace = request[1].decode()
                i = None
                try:
                    i = int(namespace)
                except BaseException:
                    pass

                if i is not None:
                    # means is selection of DB in redis directly because is int
                    response.encode("OK")
                    continue

                socket.namespace = namespace
                if socket.namespace not in j.servers.gedis.latest.namespaces:
                    response.error("could not find namespace:%s" % socket.namespace)
                    continue

                self.logger.debug("NAMESPACE_%s_%s" % (address, socket.namespace))
                response.encode("OK")
                continue

            if redis_cmd == "command":
                response.encode("OK")
                continue

            if redis_cmd == "ping":
                response.encode("PONG")
                continue

            namespace, actor, command = self.command_split(redis_cmd, namespace=socket.namespace)
            self.logger.debug("cmd:%s:%s:%s" % (namespace, actor, command))

            cmd, err = self.command_obj_get(cmd=command, namespace=namespace, actor=actor)
            if err:
                response.error(err)
                self.logger.debug("error:%s" % err)
                continue

            params = {}
            content_type = 'auto'
            response_type = 'auto'
            if cmd.schema_in:
                if len(request) < 2:
                    response.error("can not handle with request, not enough arguments")
                    continue
                header = None
                # If request length is > 2 we will expect a header
                if len(request) > 2:
                    try:
                        header = j.data.serializers.json.loads(request[2])
                    except BaseException:
                        response.error("Invalid header was provided, "
                                       "the header should be a json object with the key header, "
                                       "e.g: {'content_type':'json', 'response_type':'capnp'})")
                if header:
                    if 'content_type' in header:
                        content_type = header['content_type']
                    if 'response_type' in header:
                        response_type = header['response_type']
                if content_type.casefold() == 'auto':
                    try:
                        # Try capnp
                        id, data = j.data.serializers.msgpack.loads(request[1])
                        o = cmd.schema_in.get(capnpbin=data)
                        if id:
                            o.id = id
                        content_type = 'capnp'
                    except BaseException:
                        # Try Json
                        o = cmd.schema_in.get(data=j.data.serializers.json.loads(request[1]))
                        content_type = 'json'

                elif content_type.casefold() == 'json':
                    try:
                        o = cmd.schema_in.get(data=j.data.serializers.json.loads(request[1]))
                    except BaseException:
                        response.error("the content is not valid json while you provided content_type=json")
                elif content_type.casefold() == 'capnp':
                    try:
                        id, data = j.data.serializers.msgpack.loads(request[1])
                        o = cmd.schema_in.get(capnpbin=data)
                        if id:
                            o.id = id
                    except BaseException:
                        response.error("the content is not valid capnp while you provided content_type=capnp")
                else:
                    response.error("invalid content type was provided the valid types are ['json', 'capnp', 'auto']")

                args = [a.strip() for a in cmd.cmdobj.args.split(',')]
                if 'schema_out' in args:
                    args.remove('schema_out')

                schema_dict = o._ddict
                if len(args) == 1:
                    if args[0] in schema_dict:
                        params.update(schema_dict)
                    else:
                        params[args[0]] = o
                else:
                    params.update(schema_dict)

            else:
                if len(request) > 1:
                    params = request[1:]

            if cmd.schema_out:
                params["schema_out"] = cmd.schema_out

            self.logger.debug("execute command callback:%s:%s" % (cmd, params))
            result = None
            try:
                if params == {}:
                    result = cmd.method()
                elif j.data.types.list.check(params):
                    self.logger.debug("PARAMS:%s" % params)
                    result = cmd.method(*params)
                else:
                    result = cmd.method(**params)
                # self.logger.debug("Callback done and result {} , type {}".format(result, type(result)))
            except Exception as e:
                self.logger.debug("exception in redis server")
                j.errorhandler.try_except_error_process(e, die=False)
                msg = str(e)
                msg += "\nCODE:%s:%s\n" % (cmd.namespace, cmd.name)
                response.error(msg)
                continue
            # self.logger.debug("response:{}:{}:{}".format(address, cmd, result))

            if cmd.schema_out:
                if (response_type == 'auto' and content_type == 'capnp') or response_type == 'capnp':
                    result = result._data
            print("content_type: {}, response_type: {}".format(content_type, response_type))
            response.encode(result)

    def command_split(self, cmd, actor="system", namespace="system"):
        self.logger.debug("cmd_start:%s:%s:%s" % (namespace, actor, cmd))
        cmd_parts = cmd.split(".")
        if len(cmd_parts) == 3:
            namespace = cmd_parts[0]
            actor = cmd_parts[1]
            if "__" in actor:
                actor = actor.split("__", 1)[1]
            cmd = cmd_parts[2]

        elif len(cmd_parts) == 2:
            actor = cmd_parts[0]
            if "__" in actor:
                actor = actor.split("__", 1)[1]
            cmd = cmd_parts[1]
            if actor == "system":
                namespace = "system"
        elif len(cmd_parts) == 1:
            namespace = "system"
            actor = "system"
            cmd = cmd_parts[0]
        else:
            raise RuntimeError("cmd not properly formatted")

        return namespace, actor, cmd

    def command_obj_get(self, namespace, actor, cmd):
        self.logger.debug('command cache miss:%s %s %s' % (namespace, actor, cmd))

        key = "%s__%s" % (namespace, actor)
        key_cmd = "%s__%s" % (key, cmd)

        # caching so we don't have to eval every time
        if key_cmd in self.cmds:
            return self.cmds[key_cmd], ''

        if namespace == "system" and key not in self.classes:
            # we will now check if the info is in default namespace
            key = "default__%s" % actor
        if namespace == "default" and key not in self.classes:
            # we will now check if the info is in system namespace
            key = "system__%s" % actor

        if key not in self.classes:
            return None, "Cannot find cmd with key:%s in classes" % key

        if key not in self.cmds_meta:
            return None, "Cannot find cmd with key:%s in cmds_meta" % key

        meta = self.cmds_meta[key]

        # check cmd exists in the metadata
        if cmd not in meta.cmds:
            return None, "Cannot find method with name:%s in namespace:%s" % (cmd, namespace)

        cmd_obj = meta.cmds[cmd]

        try:
            cl = self.classes[key]
            cmd_method = getattr(cl, cmd)
        except Exception as e:
            return None, "Could not execute code of method '%s' in namespace '%s'\n%s" % (key, namespace, e)

        cmd_obj.method = cmd_method
        self.cmds[key_cmd] = cmd_obj

        return self.cmds[key_cmd], ""

    # def handle_websocket(self,socket, namespace):
    #
    #     message = socket.receive()
    #     if not message:
    #         return
    #     message = json.loads(message)
    #     namespace,actor,cmd = self.command_split(message["command"],namespace=namespace)
    #     cmd, err = self.command_obj_get(namespace,actor,cmd)
    #     if err:
    #         socket.send(err)
    #         return
    #
    #     res, err = self.handle_websocket_(cmd, message,namespace=namespace)
    #     if err:
    #         socket.send(err)
    #         return
    #
    #     socket.send(json.dumps(res))
    #
    # def handle_websocket_(self, cmd, message,namespace):
    #
    #     if cmd.schema_in:
    #         if not message.get("args"):
    #             return None, "need to have arguments, none given"
    #
    #         o = cmd.schema_in.get(data=j.data.serializers.json.loads(message["args"]))
    #         args = [a.strip() for a in cmd.cmdobj.args.split(',')]
    #         if 'schema_out' in args:
    #             args.remove('schema_out')
    #         params = {}
    #         schema_dict = o._ddict
    #         if len(args) == 1:
    #             if args[0] in schema_dict:
    #                 params.update(schema_dict)
    #             else:
    #                 params[args[0]] = o
    #         else:
    #             params.update(schema_dict)
    #
    #         if cmd.schema_out:
    #             params["schema_out"] = cmd.schema_out
    #     else:
    #         if message.get("args"):
    #             params = message["args"]
    #             if cmd.schema_out:
    #                 params.append(cmd.schema_out)
    #         else:
    #             params = None
    #
    #     try:
    #         if params is None:
    #             result = cmd.method()
    #         elif j.data.types.list.check(params):
    #             result = cmd.method(*params)
    #         else:
    #             result = cmd.method(**params)
    #         return result, None
    #
    #     except Exception as e:
    #         self.logger.debug("exception in redis server")
    #         eco = j.errorhandler.parsePythonExceptionObject(e)
    #         msg = str(eco)
    #         msg += "\nCODE:%s:%s\n" % (cmd.namespace, cmd.name)
    #         self.logger.debug(msg)
    #         return None, e.args[0]
