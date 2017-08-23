# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Abort(object):
    WAMP_CODE = 3
    name = "abort"

    def __init__(self, details=None, uri=None):
        """ Sent by a Peer*to abort the opening of a WAMP session.

        No response is expected.

        :Parameters:
            details  : dict
            uri : string

        [ABORT, Details|dict, Reason|uri]

        """
        super(Abort, self).__init__()

        self.details = details
        self.uri = uri

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.details, self.uri
        ]
