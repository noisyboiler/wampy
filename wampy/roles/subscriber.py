from wampy.errors import WampyError
from wampy.messages.subscribe import Subscribe


class SubscriberMixin(object):

    def subscribe(self, topic, handler):
        entrypoint_name = handler.func_name
        message = Subscribe(topic=topic)

        response_msg = self.send_message_and_wait_for_response(message)
        _, _, subscription_id = response_msg

        self.subscription_map[entrypoint_name] = subscription_id, topic

        self.logger.info(
            'registering entrypoint "%s (%s)" for subscriber "%s"',
            entrypoint_name, topic, self.name
        )


class RegisterSubscriptionDecorator(object):

    def __init__(self, **kwargs):
        if "topic" not in kwargs:
            raise WampyError(
                "subscriber missing ``topic`` keyword argument"
            )

        self.topic = kwargs['topic']

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            f(*args, **kwargs)

        wrapped_f.subscriber = True
        wrapped_f.topic = self.topic
        wrapped_f.handler = f
        return wrapped_f

subscribe = RegisterSubscriptionDecorator
