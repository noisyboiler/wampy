# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

logger = logging.getLogger(__name__)


class Welcome(object):
    """ A _Router_ completes the opening of a WAMP session by sending a
   "WELCOME" reply message to the _Client_.

       [WELCOME, Session|id, Details|dict]

    """
    WAMP_CODE = 2
    name = "welcome"

    def __init__(self, session_id, details_dict):
        self.session_id = session_id
        self.details = details_dict

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.session_id, self.details,
        ]
