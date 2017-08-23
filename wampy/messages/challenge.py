# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Challenge(object):
    WAMP_CODE = 4
    name = "challenge"

    def __init__(self, auth_method, kwargs_dict):
        """ The "CHALLENGE" message is used with certain Authentication
        Methods. During authenticated session establishment, a *Router*
        sends a challenge message.

            [CHALLENGE, AuthMethod|string, Extra|dict]

        """
        super(Challenge, self).__init__()

        self.auth_method = auth_method
        self.kwargs_dict = kwargs_dict

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.auth_method, self.kwargs_dict
        ]

    @property
    def value(self):
        return self.kwargs_dict

    @property
    def challenge(self):
        return self.value['challenge']
