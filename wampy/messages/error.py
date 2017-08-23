# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from wampy.errors import WampyError


class Error(object):
    WAMP_CODE = 8
    name = "error"

    def __init__(
            self, request_type, request_id,
            details=None, error="", args_list=None, kwargs_dict=None
    ):
        """ Error reply sent by a Peer as an error response to
        different kinds of requests.

        :Parameters:

            :request_type:
                The WAMP message type code for the original request.
            :type request_type: int

            :request_id:
                The WAMP request ID of the original request
                (`Call`, `Subscribe`, ...) this error occurred for.
            :type request: int

            :args_list:
                Args to pass into an Application defined Exception

            :kwargs_list:
                Kwargs to pass into an Application defined Exception

            [ERROR, REQUEST.Type|int, REQUEST.Request|id, Details|dict,
                Error|uri, Arguments|list, ArgumentsKw|dict]

        """
        super(Error, self).__init__()

        self.request_type = request_type
        self.request_id = request_id
        self.error = error
        self.args_list = args_list or []
        self.kwargs_dict = kwargs_dict or {}

        # wampy is not implementing ``details`` which appears to be an
        # alternative to args and kwargs
        if details:
            raise WampyError(
                "Not Implemented: must use ``args_list`` and '"
                "``kwargs_dict, not ``details``"
            )
        self.details = {}

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.request_type, self.request_id,
            self.details, self.error, self.args_list, self.kwargs_dict,
        ]
