# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Invocation(object):
    """Actual invocation of an endpoint sent by Dealer to a Callee.

       [INVOCATION, Request|id, REGISTERED.Registration|id,
           Details|dict]

       [INVOCATION, Request|id, REGISTERED.Registration|id,
           Details|dict, C* Arguments|list]

       [INVOCATION, Request|id, REGISTERED.Registration|id,
           Details|dict, CALL.Arguments|list, CALL.ArgumentsKw|dict]

    """
    WAMP_CODE = 68
    name = "invocation"

    def __init__(
            self, request_id, registration_id, details,
            call_args=None, call_kwargs=None,
    ):

        super(Invocation, self).__init__()

        self.request_id = request_id
        self.registration_id = registration_id
        self.details = details
        self.call_args = call_args or tuple()
        self.call_kwargs = call_kwargs or {}

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.request_id, self.registration_id,
            self.details, self.call_args, self.call_kwargs,
        ]
