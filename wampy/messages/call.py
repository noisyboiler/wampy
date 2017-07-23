# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random


class Call(object):
    """ When a Caller wishes to call a remote procedure, it sends a "CALL"
    message to a Dealer.

    Message is of the format
    ``[CALL, Request|id, Options|dict, Procedure|uri, Arguments|list,
    ArgumentsKw|dict]``, e.g. ::

        [
            CALL, 10001, {}, "com.myapp.myprocedure1", [], {}
        ]

    "Request" is a random, ephemeral ID chosen by the Callee and
    used to correlate the Dealer's response with the request.

    "Options" is a dictionary that allows to provide additional
    registration request details in a extensible way.

    """
    WAMP_CODE = 48
    name = "call"

    def __init__(self, procedure, options=None, args=None, kwargs=None):
        super(Call, self).__init__()

        self.procedure = procedure
        self.options = options or {}
        self.args = args or []
        self.kwargs = kwargs or {}
        self.request_id = random.getrandbits(32)

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.request_id, self.options, self.procedure,
            self.args, self.kwargs
        ]
