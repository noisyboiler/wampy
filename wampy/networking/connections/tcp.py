import socket

from ... constants import DEFAULT_HOST, DEFAULT_PORT
from ... exceptions import ConnectionError
from ... logger import get_logger


logger = get_logger('wampy.networking.connections.tcp')


class TCPConnection(object):
    """ A TCP socket connection
    """
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None

    def _connect(self):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.host, self.port))
        self.socket = _socket

    def connect(self):
        self._connect()

    def recv(self):
        received_bytes = bytearray()

        while True:
            bytes = self._recv()
            if not bytes:
                break

            received_bytes.extend(bytes)

        return received_bytes

    def send(self, message):
        self.socket.sendall(message)

    def _recv(self, bufsize=1024):
        try:
            bytes = self.socket.recv(bufsize)
        except socket.timeout as e:
            message = str(e)
            raise ConnectionError('timeout: "{}"'.format(message))

        return bytes
