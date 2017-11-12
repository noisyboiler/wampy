# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Pong(object):
    """ Send pong message to the Router.

    Message is of the format ``[PONG, challenge]``, e.g. ::

        [
            PONG, 0xcaffffee
        ]

    """
    WAMP_CODE = -2
    name = "pong"

    def __init__(self, challenge):
        super(Pong, self).__init__()

        self.challenge = challenge

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.challenge
        ]
