from Jumpscale import j

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
        self.namespace = "system"

    def _handle_request(self, socket, address):
        self.logger.info('connection from {}'.format(address))
        self.parser = self.get_parser(socket)
        self.response = self.get_response(socket)

        while True:
            request = self.parser.read_request()

            if request is None:
                break

            if not request:  # empty list request
                # self.response.error('Empty request body .. probably this is a (TCP port) checking query')
                continue

            cmd = request[0]
            redis_cmd = cmd.decode("utf-8").lower()

            #special command to put the client on right namespace
            if redis_cmd == "select":
                self.namespace = params[0].decode()
                return self.response.encode("OK")

            params = {}

            cmd, err = self.get_command(redis_cmd)
            if err is not "":
                self.response.error(err)
                continue
            if cmd.schema_in:
                if len(request) < 2:
                    self.response.error("can not handle with request, not enough arguments")
                    continue
                if len(request) > 2:
                    cmd.schema_in.properties
                    print("more than 1 input")
                    self.response.error("more than 1 argument given, needs to be binary capnp message or json")
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
                self.response.error(msg)
                continue
            self.logger.debug(
                "response:{}:{}:{}".format(address, cmd, result))

            if cmd.schema_out:
                result = self.encode_result(result)
            self.response.encode(result)

    def get_command(self, cmd):

        self.logger.debug('(%s) command cache miss')

        if cmd=="auth":
            namespace = "system"
            actor = "system"
        elif '.' in cmd:
            splitted = cmd.split(".", 1)
            if len(splitted)==2:
                namespace = self.namespace
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
            return None, "Cannot find method with name:%s in namespace:%s" % (post, namespace)

        cmd_obj = meta.cmds[cmd]

        try:
            cl = self.classes[key]
            m = eval("cl.%s" % (cmd))
        except Exception as e:
            return None, "Could not execute code of method '%s' in namespace '%s'\n%s" % (pre, namespace, e)

        cmd_obj.method = m

        self.cmds[key_cmd] = cmd_obj

        return self.cmds[key_cmd], ""

    def handle(self, socket, address):
        """
        handle request
        :return:
        """
        raise NotImplementedError()

    def encode_result(self, result):
        """
        Get data format to be sent to client
        ie capnp or json according to Handler type used
        """
        raise NotImplementedError()

    def encode_error(self, err):
        """
        Get error format to be sent to client
        """
        raise NotImplementedError()

    def get_parser(self, socket):
        raise NotImplementedError()

    def get_response(self, socket):
        raise NotImplementedError()


class RedisRequestHandler(Handler):
    def handle(self, socket, address):
        try:
            self._handle_request(socket, address)
        except ConnectionError as err:
            self.logger.info('connection error: {}'.format(str(err)))
        finally:
            self.parser.on_disconnect()
            self.logger.info('close connection from {}'.format(address))

    def encode_result(self, result):
        if hasattr(result, "_data"):
            return result._data
        else:
            return str(result).encode()

    def encode_error(self, error):
        return error

    def get_parser(self, socket):
        return RedisCommandParser(socket)

    def get_response(self, socket):
        return RedisResponseWriter(socket)


class WebsocketRequestHandler(Handler):
    def handle(self, socket, address):
        try:
            self._handle_request(socket, address)
        except WebSocketError as err:
            self.logger.info('connection error: {}'.format(str(err)))
        finally:
            self.logger.info('close connection from {}'.format(address))

    def encode_result(self, result):
        return result

    def encode_error(self, error):
        return error.encode('utf-8')

    def get_parser(self, socket):
        return WebsocketsCommandParser(socket)

    def get_response(self, socket):
        return WebsocketResponseWriter(socket)
