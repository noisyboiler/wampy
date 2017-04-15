from wampy.errors import WampProtocolError
from wampy.messages.message import Message


class Subscribed(Message):
    """ If the _Broker_ is able to fulfill and allow the subscription, it
    answers by sending a "SUBSCRIBED" message to the _Subscriber_

       [SUBSCRIBED, SUBSCRIBE.Request|id, Subscription|id]

    """
    WAMP_CODE = 33

    def __init__(self, wamp_code, request_id, subscription_id):
        self.wamp_code = wamp_code
        self.request_id = request_id
        self.subscription_id = subscription_id

    @property
    def message(self):
        return [
            self.wamp_code, self.request_id, self.subscription_id,
        ]

    def process(self, client):
        session = client.session

        if self.wamp_code != Message.SUBSCRIBED:
            raise WampProtocolError(
                'failed to subscribe to topic: "{}"'.format(self.message)
            )

        original_message, procedure_name = client.request_ids[self.request_id]
        topic = original_message.topic

        session.subscription_map[self.subscription_id] = procedure_name, topic
