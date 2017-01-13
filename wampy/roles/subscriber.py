import logging

from wampy.peers.clients import Client
from wampy.peers.routers import Router
from wampy.errors import WampyError

logger = logging.getLoggger(__name__)


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


class Subscriber(object):
    """ Stand alone websocket topic subscriber """

    def __init__(self, router, realm, topic, roles=None):
        self.router = router if isinstance(router, Router) else router()
        self.realm = realm
        self.topic = topic
        self.roles = roles or {
            'roles': {
                'subscriber': {},
            },
        }
        self.client = Client(
            roles=self.roles, realm=self.realm, router=self.router)

    def connect(self):
        # TODO: now a use-case for a slimmed down Client???
        self.client.start_session()

    def topic_handler(self, *args, **kwargs):
        logger.info(
            "handling message from %s topic: (%s, %s)",
            self.topic, args, kwargs
        )

    def subscribe(self):
        self.client._subscribe(topic=self.topic, handler=self.topic_handler)
