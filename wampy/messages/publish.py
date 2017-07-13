# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random

from wampy.messages.message import Message


class Publish(Message):
    """ Send a PUBLISH message to the Router.

    Message is of the format ``[PUBLISH, Request|id, Options|dict,
    Topic|uri, Arguments|list, ArgumentsKw|dict]``, e.g. ::

        [
            16, 239714735, {}, "com.myapp.mytopic1", [],
            {"color": "orange", "sizes": [23, 42, 7]}
        ]

    """
    WAMP_CODE = 16
    name = "publish"

    def __init__(self, topic, options, *args, **kwargs):
        super(Publish, self).__init__()

        self.topic = topic
        self.options = options
        self.request_id = random.getrandbits(32)
        self.args = args
        self.kwargs = kwargs
        self.message = [
            Message.PUBLISH, self.request_id, self.options, self.topic,
            self.args, self.kwargs
        ]
