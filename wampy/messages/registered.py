# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Registered(object):
    """ [REGISTERED, REGISTER.Request|id, Registration|id]
    """
    WAMP_CODE = 65
    name = "registered"

    def __init__(self, request_id, registration_id):

        super(Registered, self).__init__()

        self.request_id = request_id
        self.registration_id = registration_id

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.request_id, self.registration_id,
        ]
