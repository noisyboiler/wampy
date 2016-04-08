from ... constants import WEBSOCKET_SUBPROTOCOLS
from ... logger import get_logger
from . websocket import WebsocketConnection


logger = get_logger('wampy.networking.connections.wamp')


class WampConnection(WebsocketConnection):
    type_ = 'wamp'

    def __init__(self, host, port):
        super(WampConnection, self).__init__(host, port)

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
        headers = self._get_handshake_headers()
        handshake = '\n\r'.join(headers) + "\r\n\r\n"
        self.socket.send(handshake)
        self.status, self.headers = self._read_handshake_response()

        logger.info('Wamp Connection status: "%s"', self.status)
        logger.info(self.headers)
