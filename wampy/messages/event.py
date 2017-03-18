from wampy.errors import WampError
from wampy.messages.message import Message


class Event(Message):
    """ When a Subscriber_is deemed to be a receiver, the Broker sends
    the Subscriber an "EVENT" message:

        [EVENT, SUBSCRIBED.Subscription|id, PUBLISHED.Publication|id,
         Details|dict]

            or

        [EVENT, SUBSCRIBED.Subscription|id, PUBLISHED.Publication|id,
               Details|dict, PUBLISH.Arguments|list]

            or

        [EVENT, SUBSCRIBED.Subscription|id, PUBLISHED.Publication|id,
         Details|dict, PUBLISH.Arguments|list, PUBLISH.ArgumentKw|dict]

    """
    WAMP_CODE = 36

    def __init__(
            self, wamp_code, subscription_id, publication_id, details_dict,
            publish_args=None, publish_kwargs=None,
    ):

        assert wamp_code == self.WAMP_CODE

        self.subscription_id = subscription_id
        self.publication_id = publication_id
        self.details = details_dict
        self.publish_args = publish_args or []
        self.publish_kwargs = publish_kwargs or {}

        self.message = [
            self.WAMP_CODE, self.subscription_id, self.publication_id,
            self.details, self.publish_args, self.publish_kwargs,
        ]

    def process(self, message, client):
        session = client.session

        payload_list = []
        payload_dict = {}

        try:
            # [
            #   EVENT,
            #   SUBSCRIBED.Subscription|id,
            #   PUBLISHED.Publication|id,
            #   Details|dict,
            #   PUBLISH.Arguments|list,
            #   PUBLISH.ArgumentKw|dict]
            # ]
            _, subscription_id, _, details, payload_list, payload_dict = (
                message)
        except ValueError:

            try:
                # [
                #   EVENT,
                #   SUBSCRIBED.Subscription|id,
                #   PUBLISHED.Publication|id,
                #   Details|dict,
                #   PUBLISH.Arguments|list,
                # ]
                _, subscription_id, _, details, payload_list = message
            except ValueError:
                # [
                #   EVENT,
                #   SUBSCRIBED.Subscription|id,
                #   PUBLISHED.Publication|id,
                #   Details|dict,
                # ]
                _, subscription_id, _, details = message

        func_name, topic = session.subscription_map[subscription_id]
        try:
            func = getattr(client, func_name)
        except AttributeError:
            raise WampError(
                "Event handler not found: {}".format(func_name)
            )

        payload_dict['meta'] = {}
        payload_dict['meta']['topic'] = topic
        payload_dict['meta']['subscription_id'] = subscription_id

        func(*payload_list, **payload_dict)
