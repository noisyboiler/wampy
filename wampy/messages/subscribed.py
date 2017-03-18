from wampy.errors import WampProtocolError
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

    def process(self, message, client):
        session = client.session

        wamp_code, request_id, subscription_id = message
        if wamp_code != Message.SUBSCRIBED:
            raise WampProtocolError(
                'failed to subscribe to topic: "{}"'.format(message)
            )

        original_message, procedure_name = client.request_ids[request_id]
        topic = original_message.topic

        session.subscription_map[subscription_id] = procedure_name, topic
