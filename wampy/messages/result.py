# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Result(object):
    """ The Dealer sends a "RESULT" message to the original
    Caller ::

           [RESULT, CALL.Request|id, Details|dict]

        or

           [RESULT, CALL.Request|id, Details|dict, YIELD.Arguments|list]

        or

           [RESULT, CALL.Request|id, Details|dict, YIELD.Arguments|list,
               YIELD.ArgumentsKw|dict]

    """
    WAMP_CODE = 50
    name = "result"

    def __init__(
            self, request_id, details_dict, yield_args=None,
            yield_kwargs=None
    ):

        super(Result, self).__init__()

        self.request_id = request_id
        self.details = details_dict
        self.yield_args = yield_args
        self.yield_kwargs = yield_kwargs

    def __str__(self):
        return str(self.message)

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.request_id, self.details, self.yield_args,
            self.yield_kwargs
        ]

    @property
    def value(self):
        if self.yield_kwargs:
            return self.yield_kwargs['message']
        return self.yield_args[0]
