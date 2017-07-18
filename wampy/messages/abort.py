# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from wampy.messages.message import Message


class Abort(Message):
    WAMP_CODE = 3
    name = "abort"

    def __init__(self, wamp_code, details=None, uri=None):
        """ Sent by a Peer*to abort the opening of a WAMP session.

        No response is expected.

        :Parameters:
            details  : dict
            uri : string

        [ABORT, Details|dict, Reason|uri]

        """
        assert wamp_code == self.WAMP_CODE
        super(Abort, self).__init__()

        self.details = details
        self.uri = uri
        self.message = [
            self.WAMP_CODE, self.details, self.uri
        ]
