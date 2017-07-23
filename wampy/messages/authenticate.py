# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Authenticate(object):
    WAMP_CODE = 5
    name = "authenticate"

    def __init__(self, signature, kwargs_dict=None):
        """ The "AUTHENTICATE" message is used with certain Authentication
        Methods.  A *Client* having received a challenge is expected to
        respond by sending a signature or token.

            [AUTHENTICATE, Signature|string, Extra|dict]

        """
        super(Authenticate, self).__init__()

        self.signature = signature
        self.kwargs_dict = kwargs_dict or {}

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.signature, self.kwargs_dict
        ]
