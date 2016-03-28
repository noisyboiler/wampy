import socket
from socket import error as socket_error

from ... constants import DEFAULT_HOST, DEFAULT_PORT
from ... exceptions import ConnectionError
from ... helpers import collect_configuration
from ... logger import get_logger


logger = get_logger('wampy.networking.connections.tcp')


class TCPConnection(object):
    """ A TCP socket connection
    """
    def __init__(self, config=None):
        _config = config or collect_configuration()
        router = _config['peers']['router']

        self.host = router.get('host', DEFAULT_HOST)
        self.port = router.get('port', DEFAULT_PORT)
        self.config = _config
        self.socket = None

    def _connect(self):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.info('attempting connection to %s:%s', self.host, self.port)

        try:
            _socket.connect((self.host, self.port))
        except socket_error as exc:
            if exc.errno == 61:
                logger.warning(
                    'unable to connect to %s:%s', self.host, self.port)
            logger.error(exc)
            raise

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
