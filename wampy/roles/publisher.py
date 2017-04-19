import logging

from wampy.errors import WampyError
from wampy.messages.publish import Publish


logger = logging.getLogger('wampy.publishing')


class PublishProxy:

    def __init__(self, client):
        self.client = client

    def __call__(self, *unsupported_args, **kwargs):
        if len(unsupported_args) != 0:
            raise WampyError(
                "wampy only supports publishing keyword arguments "
                "to a Topic."
            )

        topic = kwargs.pop("topic")
        if not kwargs:
            raise WampyError(
                "wampy requires at least one message to publish to a topic"
            )

        message = Publish(topic=topic, options={}, **kwargs)
        logger.info('publishing message: "%s"', message)

        self.client.send_message(message)
