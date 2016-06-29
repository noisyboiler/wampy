class ConfigurationError(Exception):
    pass


class ConnectionError(Exception):
    pass


class IncompleteFrameError(Exception):
    pass


class MessageRouterConnectionError(Exception):
    pass


class SessionError(Exception):
    pass


class WampProtocolError(Exception):
    pass


class WebsocktProtocolError(Exception):
    pass


class ProcedureNotFoundError(AttributeError):
    pass


class WampError(Exception):
    pass
