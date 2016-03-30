class ConfigurationError(Exception):
    pass


class ConnectionError(Exception):
    pass


class IncompleteFrameError(Exception):
    pass


class MessageRouterConnectionError(Exception):
    pass


class WampProtocolError(Exception):
    pass


class WebsocktProtocolError(Exception):
    pass
