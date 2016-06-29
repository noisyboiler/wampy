import logging

from ... constants import WEBSOCKET_SUBPROTOCOLS
from . websocket import WebsocketConnection


logger = logging.getLogger(__name__)


class WampConnection(WebsocketConnection):
    type_ = 'wamp'

    def __init__(self, host, port, websocket_location="ws"):
        super(WampConnection, self).__init__(host, port, websocket_location)

    def _get_handshake_headers(self):
        """ Do an HTTP upgrade handshake with the server.

        The headers here will go a little further and also agree the
        WAMP websocket JSON subprotocols.

        """
        headers = super(WampConnection, self)._get_handshake_headers()
        headers.append("Sec-WebSocket-Protocol: {}".format(
            WEBSOCKET_SUBPROTOCOLS))

        return headers

    def _upgrade(self):
        handshake_headers = self._get_handshake_headers()
        handshake = '\r\n'.join(handshake_headers) + "\r\n\r\n"

        logger.debug("WAMP Connection handshake: %s", ', '.join(
            handshake_headers))

        self.socket.send(handshake)
        self.status, self.headers = self._read_handshake_response()

        logger.debug("WAMP Connection reply: %s", self.headers)
