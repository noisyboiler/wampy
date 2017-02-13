from wampy.messages.message import Message


class Subscribed(Message):
    """ If the _Broker_ is able to fulfill and allow the subscription, it
    answers by sending a "SUBSCRIBED" message to the _Subscriber_

       [SUBSCRIBED, SUBSCRIBE.Request|id, Subscription|id]

    """
    WAMP_CODE = 33

    def __init__(self, wamp_code, request_id, subscription_id):
        assert wamp_code == self.WAMP_CODE

        self.request_id = request_id
        self.subscription_id = subscription_id

        self.message = [
            self.WAMP_CODE, self.request_id, self.subscription_id,
        ]
