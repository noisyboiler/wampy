# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random


class Subscribe(object):
    """ Send a SUBSCRIBE message to the Router.

    Message is of the format ``[SUBSCRIBE, Request|id, Options|dict,
    Topic|uri]``, e.g. ::

        [
            32, 713845233, {}, "com.myapp.mytopic1"
        ]

    """
    WAMP_CODE = 32
    name = "subscribe"

    def __init__(self, topic, options=None):
        super(Subscribe, self).__init__()

        self.topic = topic
        self.options = options or {}
        self.request_id = random.getrandbits(32)

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.request_id, self.options, self.topic
        ]
