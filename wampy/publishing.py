import logging

from . messages.publish import Publish


logger = logging.getLogger('wampy.publishing')


class PublishProxy:

    def __init__(self, client):
        self.client = client

    def __call__(self, topic, *args, **kwargs):
        message = Publish(topic=topic, options={}, **kwargs)
        logger.info(
            '%s publishing message: "%s"', self.client.name, message
        )

        self.client.send_message(message)


class RegisterSubscriptionDecorator(object):

    def __init__(self, *args, **kwargs):
        # If there are decorator arguments, the function
        # to be decorated is not passed to the constructor!
        self.args = args
        self.kwargs = kwargs

    def __call__(self, f):
        # If there are decorator arguments, __call__() is only called
        # once, as part of the decoration process! You can only give
        # it a single argument, which is the function object.
        def wrapped_f(*args, **kwargs):
            f(*args, **kwargs)

        wrapped_f.subscriber = True
        wrapped_f.topic = self.kwargs['topic']
        wrapped_f.handler = f
        return wrapped_f

subscriber = RegisterSubscriptionDecorator
