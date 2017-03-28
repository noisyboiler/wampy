class ConfigurationError(Exception):
    pass


class ConnectionError(Exception):
    pass


class IncompleteFrameError(Exception):
    def __init__(self, required_bytes):
        self.required_bytes = required_bytes


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


class WampyError(Exception):
    pass
