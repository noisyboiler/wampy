# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Cancel(object):
    """ When a Caller wishes to cancel a remote procedure, it sends a "CANCEL"
    message to the Dealer.

    Message is of the format
    ``[CANCEL, CALL.Request|id, Options|dict]``, e.g. ::

        [
            CANCEL, 10001, {},
        ]

    "Request" is the ID used to make the Call being cancelled.

    "Options" is a dictionary that allows to provide additional
    cancellation request details in a extensible way.

    """
    WAMP_CODE = 49
    name = "cancel"

    def __init__(self, request_id, options=None):
        super(Cancel, self).__init__()

        self.request_id = request_id
        self.options = options or {}

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.request_id, self.options,
        ]
