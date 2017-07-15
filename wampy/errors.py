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


class WelcomeAbortedError(WampProtocolError):
    pass


class RemoteError(Exception):
    def __init__(self, remote_api, request_id, *args, **kwargs):
        self.remote_api = remote_api
        self.request_id = request_id
        self.exc_type = kwargs.get("exc_type")
        self.value = kwargs.get("message")

        message = '{} [{}] failed with reason {} {}'.format(
            self.remote_api, self.request_id, self.exc_type, self.value)
        super(RemoteError, self).__init__(message)


class NotAuthorisedError(Exception):
    pass
