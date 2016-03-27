from ... constants import (
    DEFAULT_REALM, DEFAULT_ROLES, WEBSOCKET_SUBPROTOCOLS)
from ... logger import get_logger
from . websocket import WebsocketConnection


logger = get_logger('wampy.networking.connections.wamp')


class WampConnection(WebsocketConnection):
    def __init__(self, host, port, realm=DEFAULT_REALM, roles=DEFAULT_ROLES):
        super(WampConnection, self).__init__(host, port)

        self.realm = realm
        self.roles = roles
        self.websocket_wamp_connected = False

    def _get_handshake_headers(self):
        """ Do an HTTP upgrade handshake with the server.

        The headers here will go a little further and also agree the
        WAMP websocket JSON subprotocols.

        """
        headers = super(WampConnection, self)._get_handshake_headers()
        headers.append("Sec-WebSocket-Protocol: %s" % WEBSOCKET_SUBPROTOCOLS)
        return headers
