import logging

from wampy.errors import WampyError
from wampy.peers.clients import Client

logger = logging.getLogger(__name__)


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


class TopicSubscriber(Client):
    """ Stand alone websocket topic subscriber """

    DEFAULT_ROLES = {
        'roles': {
            'subscriber': {},
        },
    }

    def __init__(
        self, topics, callback, router, roles=None, name=None,
    ):
        """ Subscribe to a one or more topics.

        :Parameters:
            topics : list of strings
            callback : func
                a callable that will do something with topic events
            router: instance
                subclass of :cls:`wampy.peers.routers.Router`
            roles: dictionary

        """
        super(TopicSubscriber, self).__init__(
            router, roles or self.DEFAULT_ROLES, name=name,
        )

        self.topics = topics
        self.callback = callback

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def start(self):
        self.session.begin()
        for topic in self.topics:
            self._subscribe_to_topic(
                topic=topic, handler=self.topic_handler
            )

        logger.info("subscribed to %s", ", ".join(self.topics))

    def stop(self):
        self.session.end()
        self.subscribed = False

    def topic_handler(self, *args, **kwargs):
        logger.info("handling message: (%s, %s)", args, kwargs)
        self.callback(*args, **kwargs)


subscribe = RegisterSubscriptionDecorator
