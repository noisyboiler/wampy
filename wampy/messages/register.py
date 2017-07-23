# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random


class Register(object):
    """ A Callee announces the availability of an endpoint implementing
    a procedure with a Dealer by sending a "REGISTER" message.

    Message is of the format
    ``[REGISTER, Request|id, Options|dict, Procedure|uri]``, e.g. ::

        [
            REGISTER, 25349185, {}, "com.myapp.myprocedure1"
        ]

    "Request" is a random, ephemeral ID chosen by the Callee and
    used to correlate the Dealer's response with the request.

    "Options" is a dictionary that allows to provide additional
    registration request details in a extensible way.

    """
    WAMP_CODE = 64
    name = "register"

    def __init__(self, procedure, options=None):
        super(Register, self).__init__()

        self.procedure = procedure
        self.options = options or {}
        self.request_id = random.getrandbits(32)

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.request_id, self.options,
            self.procedure
        ]
