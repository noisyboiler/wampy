import logging
import uuid
from base64 import encodestring

from ... constants import WEBSOCKET_VERSION
from ... exceptions import IncompleteFrameError
from .. frames import ClientFrame, ServerFrame
from . http import HttpConnection


logger = logging.getLogger(__name__)


class WebsocketConnection(HttpConnection):
    type_ = 'websocket'

    def __init__(self, host, port, websocket_location="ws"):
        super(WebsocketConnection, self).__init__(host, port)

        self.key = encodestring(uuid.uuid4().bytes).decode('utf-8').strip()
        self.websocket_location = websocket_location.lstrip('/')

    def _get_handshake_headers(self):
        """ Do an HTTP upgrade handshake with the server.

        Websockets upgrade from HTTP rather than TCP largely because it was
        assumed that servers which provide websockets will always be talking to
        a browser. Maybe a reasonable assumption once upon a time...

        """
        headers = []
        # https://tools.ietf.org/html/rfc6455
        headers.append("GET /{} HTTP/1.1".format(self.websocket_location))
        headers.append("Host: {}".format(self.host))
        headers.append("Upgrade: websocket")
        headers.append("Connection: Upgrade")
        # Sec-WebSocket-Key header containing base64-encoded random bytes,
        # and the server replies with a hash of the key in the
        # Sec-WebSocket-Accept header. This is intended to prevent a caching
        # proxy from re-sending a previous WebSocket conversation and does not
        # provide any authentication, privacy or integrity
        headers.append("Sec-WebSocket-Key: {}".format(self.key))
        headers.append("Origin: http://{}".format(self.host))
        headers.append("Sec-WebSocket-Version: {}".format(WEBSOCKET_VERSION))

        return headers

    def _upgrade(self):
        handshake_headers = self._get_handshake_headers()
        handshake = '\r\n'.join(handshake_headers) + "\r\n\r\n"

        logger.debug("WebSocket Connection handshake: %s", ', '.join(
            handshake_headers))
        self.socket.send(handshake)
        self.status, self.headers = self._read_handshake_response()

        logger.debug("WebSocket Connection reply: %s", self.headers)

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
