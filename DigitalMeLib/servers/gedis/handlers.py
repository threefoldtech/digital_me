from Jumpscale import j
import json
from redis.exceptions import ConnectionError
from geventwebsocket.exceptions import WebSocketError
from .protocol import RedisResponseWriter, RedisCommandParser, WebsocketResponseWriter, WebsocketsCommandParser

JSBASE = j.application.JSBaseClass


class Handler(JSBASE):
    def __init__(self, gedis_server):
        JSBASE.__init__(self)
        self.gedis_server=gedis_server
        self.cmds = {}            #caching of commands
        self.classes = self.gedis_server.classes
        self.cmds_meta = self.gedis_server.cmds_meta

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

        while True:
            request = parser.read_request()

            if not request:
                return

            cmd = request[0]
            redis_cmd = cmd.decode("utf-8").lower()


            params = {}

            #special command to put the client on right namespace
            if redis_cmd == "select":
                j.shell()
                socket.namespace = params[0].decode()
                return response.encode("OK")

            cmd, err = self.get_command(namespace=socket.namespace, cmd=redis_cmd)
            if err is not "":
                response.error(err)
                continue
            if cmd.schema_in:
                if len(request) < 2:
                    response.error("can not handle with request, not enough arguments")
                    continue
                if len(request) > 2:
                    cmd.schema_in.properties
                    print("more than 1 input")
                    response.error("more than 1 argument given, needs to be binary capnp message or json")
                    continue

                try:
                    # Try capnp
                    id, data = j.data.serializers.msgpack.loads(request[1])
                    o = cmd.schema_in.get(capnpbin=data)
                    if id:
                        o.id = id
                except:
                    # Try Json
                    o = cmd.schema_in.get(data=j.data.serializers.json.loads(request[1]))

                args = [a.strip() for a in cmd.cmdobj.args.split(',')]
                if 'schema_out' in args:
                    args.remove('schema_out')
                params = {}
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
                    result = cmd.method(*params)
                else:
                    result = cmd.method(**params)
                self.logger.debug("Callback done and result {} , type {}".format(result, type(result)))
            except Exception as e:
                print("exception in redis server")
                j.errorhandler.try_except_error_process(e, die=False)
                msg = str(e)
                msg += "\nCODE:%s:%s\n" % (cmd.namespace, cmd.name)
                response.error(msg)
                continue
            self.logger.debug(
                "response:{}:{}:{}".format(address, cmd, result))

            if cmd.schema_out:
                result = self.encode_result(result)
            response.encode(result)

    def get_command(self, namespace, cmd):
        self.logger.debug('(%s) command cache miss')

        if cmd=="auth":
            namespace = "system"
            actor = "system"
        elif cmd=="system.ping":
            namespace = "system"
            actor = "system"
            cmd = "ping"
        elif '.' in cmd:
            splitted = cmd.split(".", 1)
            if len(splitted)==2:
                actor = splitted[0]
                if "__" in actor:
                    actor = actor.split("__",1)[1]
                cmd = splitted[1]
            else:
                raise RuntimeError("cmd not properly formatted")
        else:
            j.shell()

        key="%s__%s"%(namespace,actor)
        key_cmd = "%s__%s"%(key,cmd)

        #caching so we don't have to eval every time
        if key_cmd in self.cmds:
            return self.cmds[key_cmd], ''

        if namespace=="system" and key not in self.classes:
            #we will now check if the info is in default namespace
            key = "default__%s" % actor
        if namespace=="default" and key not in self.classes:
            #we will now check if the info is in default namespace
            key = "system__%s" % actor

        if key not in self.classes:
            j.shell()
            return None, "Cannot find cmd with key:%s in classes" % (namespace)

        if key not in self.cmds_meta:
            j.shell()
            return None, "Cannot find cmd with key:%s in cmds_meta" % (namespace)

        meta = self.cmds_meta[key]

        #check cmd exists in the metadata
        if not cmd in meta.cmds:
            j.shell()
            return None, "Cannot find method with name:%s in namespace:%s" % (cmd, namespace)

        cmd_obj = meta.cmds[cmd]

        try:
            cl = self.classes[key]
            m = eval("cl.%s" % (cmd))
        except Exception as e:
            return None, "Could not execute code of method '%s' in namespace '%s'\n%s" % (key, namespace, e)

        cmd_obj.method = m

        self.cmds[key_cmd] = cmd_obj

        return self.cmds[key_cmd], ""


    def handle_websocket(self,socket, namespace):

        message = socket.receive()
        if not message:
            return
        message = json.loads(message)
        cmd, err = self.get_command(namespace=namespace,cmd=message["command"])
        if err:
            socket.send(err)
            return

        res, err = self.handle_websocket_(cmd, message,namespace=namespace)
        if err:
            socket.send(err)
            return

        socket.send(json.dumps(res))


    def handle_websocket_(self, cmd, message,namespace):

        if cmd.schema_in:
            if not message.get("args"):
                return None, "need to have arguments, none given"

            o = cmd.schema_in.get(data=j.data.serializers.json.loads(message["args"]))
            args = [a.strip() for a in cmd.cmdobj.args.split(',')]
            if 'schema_out' in args:
                args.remove('schema_out')
            params = {}
            schema_dict = o._ddict
            if len(args) == 1:
                if args[0] in schema_dict:
                    params.update(schema_dict)
                else:
                    params[args[0]] = o
            else:
                params.update(schema_dict)

            if cmd.schema_out:
                params["schema_out"] = cmd.schema_out
        else:
            if message.get("args"):
                params = message["args"]
                if cmd.schema_out:
                    params.append(cmd.schema_out)
            else:
                params = None

        try:
            if params is None:
                result = cmd.method()
            elif j.data.types.list.check(params):
                result = cmd.method(*params)
            else:
                result = cmd.method(**params)
            return result, None

        except Exception as e:
            print("exception in redis server")
            eco = j.errorhandler.parsePythonExceptionObject(e)
            msg = str(eco)
            msg += "\nCODE:%s:%s\n" % (cmd.namespace, cmd.name)
            print(msg)
            return None, e.args[0]

