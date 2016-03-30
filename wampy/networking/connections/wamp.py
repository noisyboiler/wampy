from ... constants import WEBSOCKET_SUBPROTOCOLS
from ... helpers import load_router_configuration
from ... logger import get_logger
from . websocket import WebsocketConnection


logger = get_logger('wampy.networking.connections.wamp')


class WampConnection(WebsocketConnection):
    type_ = 'wamp'

    def __init__(self, config=None):
        super(WampConnection, self).__init__(config)
        load_router_configuration(self.router_name, self.config)

    @property
    def router_name(self):
        return self.config['peers']['router']['name']

    @property
    def realm(self):
        return self.config['router']['realm']

    @property
    def roles(self):
        return self.config['router']['roles']

    def _get_handshake_headers(self):
        """ Do an HTTP upgrade handshake with the server.

        The headers here will go a little further and also agree the
        WAMP websocket JSON subprotocols.

        """
        headers = super(WampConnection, self)._get_handshake_headers()
        headers.append("Sec-WebSocket-Protocol: %s" % WEBSOCKET_SUBPROTOCOLS)
        return headers
