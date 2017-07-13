# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from wampy.messages.message import Message


class Subscribed(Message):
    """ If the _Broker_ is able to fulfill and allow the subscription, it
    answers by sending a "SUBSCRIBED" message to the _Subscriber_

       [SUBSCRIBED, SUBSCRIBE.Request|id, Subscription|id]

    """
    WAMP_CODE = 33
    name = "subscribed"

    def __init__(self, wamp_code, request_id, subscription_id):
        self.wamp_code = wamp_code
        self.request_id = request_id
        self.subscription_id = subscription_id

    @property
    def message(self):
        return [
            self.wamp_code, self.request_id, self.subscription_id,
        ]
