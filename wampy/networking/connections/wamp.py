from ... constants import (
    DEFAULT_REALM, DEFAULT_ROLES, WEBSOCKET_SUBPROTOCOLS)
from ... logger import get_logger
from . websocket import WebsocketConnection


logger = get_logger('wampy.networking.connections.wamp')


class WampConnection(WebsocketConnection):
    def __init__(self, config=None):
        super(WampConnection, self).__init__(config)

        router = self.config['peers']['router']
        self.realm = router.get('realm', DEFAULT_REALM)
        self.roles = router.get('roles', DEFAULT_ROLES)

    def _get_handshake_headers(self):
        """ Do an HTTP upgrade handshake with the server.

        The headers here will go a little further and also agree the
        WAMP websocket JSON subprotocols.

        """
        headers = super(WampConnection, self)._get_handshake_headers()
        headers.append("Sec-WebSocket-Protocol: %s" % WEBSOCKET_SUBPROTOCOLS)
        return headers
