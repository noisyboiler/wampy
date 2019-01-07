# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Goodbye(object):
    """ Send a GOODBYE message to the Router.

    Message is of the format ``[GOODBYE, Details|dict, Reason|uri]``, e.g. ::

        [
            GOODBYE, {}, "wamp.close.normal"
        ]

    """
    WAMP_CODE = 6
    DEFAULT_REASON = "wamp.error.close_realm"

    name = "goodbye"

    def __init__(
            self, details=None, reason=DEFAULT_REASON,
    ):

        super(Goodbye, self).__init__()

        self.details = details or {}
        self.reason = reason

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.details, self.reason
        ]
