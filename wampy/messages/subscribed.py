# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Subscribed(object):
    """ If the _Broker_ is able to fulfill and allow the subscription, it
    answers by sending a "SUBSCRIBED" message to the _Subscriber_

       [SUBSCRIBED, SUBSCRIBE.Request|id, Subscription|id]

    """
    WAMP_CODE = 33
    name = "subscribed"

    def __init__(self, request_id, subscription_id):
        super(Subscribed, self).__init__()

        self.request_id = request_id
        self.subscription_id = subscription_id

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.request_id, self.subscription_id,
        ]
