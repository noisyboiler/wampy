import logging
from uuid import uuid4

from wampy.errors import WampyError
from wampy.messages.subscribe import Subscribe
from wampy.session import session_builder

logger = logging.getLogger(__name__)


def subscribe_to_topic(session, topic, handler):
    procedure_name = handler.func_name
    message = Subscribe(topic=topic)

    session.send_message(message)
    response_msg = session.recv_message()

    _, _, subscription_id = response_msg
    session.subscription_map[procedure_name] = subscription_id, topic

    logger.info(
        'registered handler "%s" for topic "%s"', procedure_name, topic
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


class TopicSubscriber(object):
    """ Stand alone websocket topic subscriber """

    def __init__(
            self, router, realm, topic, roles=None, transport="websocket"
    ):
        """ Subscribes to a single topic on a realm on the given router.

        :Parameters:
            router: instance
            realm : string
            topic: string
            roles: dictionary

        """
        self.id = str(uuid4())
        self.router = router
        self.realm = realm
        self.topic = topic
        self.roles = roles or {
            'roles': {
                'subscriber': {},
            },
        }
        self.transport = transport

        self.session = session_builder(
            client=self, router=self.router, realm=self.realm,
            transport=self.transport)

        self.messages = []

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def start(self):
        self.session.begin()
        subscribe_to_topic(
            session=self.session, topic=self.topic, handler=self.topic_handler
        )

    def stop(self):
        self.session.end()

    def topic_handler(self, *args, **kwargs):
        logger.info(
            "handling message from %s topic: (%s, %s)",
            self.topic, args, kwargs
        )
        self.messages.append(kwargs['message'])
