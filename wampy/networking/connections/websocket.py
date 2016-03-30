import uuid
from base64 import encodestring

from ... constants import WEBSOCKET_VERSION
from ... exceptions import IncompleteFrameError
from ... logger import get_logger
from .. frames import ClientFrame, ServerFrame
from . http import HttpConnection


logger = get_logger('wampy.networking.connections.websocket')


class WebsocketConnection(HttpConnection):
    type_ = 'websocket'

    def __init__(self, config=None):
        super(WebsocketConnection, self).__init__(config)

        self.key = encodestring(uuid.uuid4().bytes).decode('utf-8').strip()
        self.data = None

    def connect(self):
        self._connect()

        headers = self._get_handshake_headers()
        handshake = '\n\r'.join(headers) + "\r\n\r\n"

        self.socket.send(handshake)
        self.status, self.headers = self._read_handshake_response()

        logger.info('Websocket Connection status: "%s"', self.status)
        logger.info(self.headers)

    def recv(self):
        received_bytes = bytearray()

        while True:
            bytes = self._recv()
            received_bytes.extend(bytes)

            try:
                frame = ServerFrame(received_bytes)
            except IncompleteFrameError:
                pass
            else:
                break

        return frame

    def send(self, message):
        frame = ClientFrame(message)
        self.socket.sendall(frame.payload)

    def _get_handshake_headers(self):
        """ Do an HTTP upgrade handshake with the server.

        Websockets upgrade from HTTP rather than TCP largely because it was
        assumed that servers which provide websockets will always be talking to
        a browser. Maybe a reasonable assumption once upon a time...

        """
        headers = []
        headers.append("GET / HTTP/1.1")
        headers.append("Host: {}:{}".format(self.host, self.port))
        headers.append("Origin: http://{}:{}".format(self.host, self.port))

        headers.append("Upgrade: websocket")
        headers.append("Connection: Upgrade")

        # Sec-WebSocket-Key header containing base64-encoded random bytes,
        # and the server replies with a hash of the key in the
        # Sec-WebSocket-Accept header. This is intended to prevent a caching
        # proxy from re-sending a previous WebSocket conversation and does not
        # provide any authentication, privacy or integrity
        headers.append("Sec-WebSocket-Key: %s" % self.key)

        headers.append("Sec-WebSocket-Version: %s" % WEBSOCKET_VERSION)
        headers.append(
            "WebSocket-Location: ws://{}:{}/ws".format(self.host, self.port)
        )

        return headers
