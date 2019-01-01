# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class ConnectionError(Exception):
    pass


class IncompleteFrameError(Exception):
    def __init__(self, required_bytes):
        self.required_bytes = required_bytes


class WampProtocolError(Exception):
    pass


class WebsocktProtocolError(Exception):
    pass


class WampyError(Exception):
    pass


class WampyTimeOutError(Exception):
    pass
