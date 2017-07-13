# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from wampy.messages.message import Message

logger = logging.getLogger(__name__)


class Registered(Message):
    """ [REGISTERED, REGISTER.Request|id, Registration|id]
    """
    WAMP_CODE = 65
    name = "registered"

    def __init__(self, wamp_code, request_id, registration_id):
        assert wamp_code == self.WAMP_CODE

        self.wamp_code = wamp_code
        self.request_id = request_id
        self.registration_id = registration_id

        self.message = [
            self.WAMP_CODE, self.request_id, self.registration_id,
        ]
