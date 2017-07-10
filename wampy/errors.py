# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


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


class RemoteError(Exception):
    pass
