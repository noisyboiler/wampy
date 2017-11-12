# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Ping(object):
    """ Received ping message from the Router.

    Message is of the format ``[PING, challenge]``, e.g. ::

        [
            PING, 0xcaffffee
        ]

    """
    WAMP_CODE = -1
    name = "ping"

    def __init__(self, challenge):
        super(Ping, self).__init__()

        self.challenge = challenge

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.challenge
        ]
