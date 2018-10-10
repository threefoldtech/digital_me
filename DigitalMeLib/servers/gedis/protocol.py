from logging import getLogger
from Jumpscale import j
from redis.connection import Encoder, PythonParser, SocketBuffer
from redis.exceptions import ConnectionError

logger = getLogger(__name__)



class RedisCommandParser(PythonParser):
    """
    Parse the command send from the client
    """

    def __init__(self, socket, socket_read_size=8192
    ):
        super(RedisCommandParser, self).__init__(
            socket_read_size=socket_read_size
        )

        self._sock = socket

        self._buffer = SocketBuffer(
            self._sock,
            self.socket_read_size
        )

        self.encoder = Encoder(
            encoding='utf-8',
            encoding_errors='strict',
            decode_responses=False
        )

    def read_request(self):
        # rename the function to map more with server side
        try:
            return self.read_response()
        except ConnectionError as e:
            logger.error('Connection err %s' % e.args)

    def request_to_dict(self,request):
        # request.pop(0) #first one is command it self
        key = None
        res={}
        for item in request:
            item = item.decode()
            if key is None:
                key = item
                continue
            else:
                key=key.lower()
                res[key] = item
                key=None
        return res




class RedisResponseWriter(object):
    """Writes data back to client as dictated by the Redis Protocol."""

    def __init__(self, socket):
        self.socket = socket
        self.dirty = True
        self.encoder = Encoder(
            encoding='utf-8',
            encoding_errors='strict',
            decode_responses=False
        )



    def encode(self, value):
        """Respond with data."""
        if isinstance(value, int):
            self._write(':%d\r\n' % value)
        elif isinstance(value, bool):
            self._write(':%d\r\n' % (1 if value else 0))
        elif isinstance(value, str):
            if "\n" in value:
                self._bulk(value)
            else:
                self._write('+%s\r\n' % value)
        elif isinstance(value, bytes):
            self._bulkbytes(value)
        elif isinstance(value, list) and value and value[0]=="*REDIS*":
            self._array(value[1:])
        elif hasattr(value, '__repr__'):
            self._bulk(value.__repr__())
        else:
            value = j.data.serializers.json.dumps(value, encoding='utf-8')
            # self._bulk(value)
            self._write('+%s\r\n' % value)

    def status(self, msg="OK"):
        """Send a status."""
        self._write("+%s\r\n" % msg)

    def error(self, msg):
        """Send an error."""
        print("###:%s"%msg)
        self._write("-ERR %s\r\n" % str(msg))

    def _bulk(self, value):
        """Send part of a multiline reply."""
        data = ["$", str(len(value)), "\r\n", value, "\r\n"]
        self._write("".join(data))

    def _array(self, value):
        """send an array."""
        data2=self.__array(value)
        self._write(data2)

    def __array(self, value):
        data = ["*", str(len(value)), "\r\n"]
        for item in value:
            if j.data.types.list.check(item):
                data.append(self.__array(item))
            else:
                data.append("+%s"%item)
            data.append("\r\n")
        data2="".join(data)
        return data2


    def _bulkbytes(self, value):
        data = [b"$", str(len(value)).encode(), b"\r\n", value, b"\r\n"]
        self._write(b"".join(data))

    def _write(self, data):
        if not self.dirty:
            self.dirty = True

        if isinstance(data, str):
            data = data.encode()
        print("SENDING {} {} on wire".format(data, type(data)))

        self.socket.sendall(data)


class WebsocketResponseWriter():
    def __init__(self, socket):
        self.socket = socket

    def encode(self, data):
        self.socket.send(j.data.serializers.json.dumps(data, encoding='utf-8'))

    def error(self, msg):
        self.socket.send(msg)