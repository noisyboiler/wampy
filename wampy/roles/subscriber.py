import logging
from uuid import uuid4

from wampy.errors import WampyError, WampProtocolError
from wampy.messages import Message
from wampy.messages.subscribe import Subscribe
from wampy.session import session_builder

logger = logging.getLogger(__name__)


def subscribe_to_topic(session, topic, handler):
    procedure_name = handler.func_name
    message = Subscribe(topic=topic)

    try:
        session.send_message(message)
        response_msg = session.recv_message()
    except Exception as exc:
        raise WampProtocolError(
            "failed to subscribe to {}: \"{}\"".format(
                topic, exc)
        )

    wamp_code, _, subscription_id = response_msg
    if wamp_code != Message.SUBSCRIBED:
        raise WampProtocolError(
            "failed to subscribe to {}: \"{}\"".format(
                topic, wamp_code)
        )

    session.subscription_map[subscription_id] = procedure_name, topic

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
            self, router, realm, topics, message_handler,
            roles=None, transport="websocket",
    ):
        """ Subscribe to a single topic.

        All messages receieved are appended to a ``message_queue`` which
        should behave like a standard Python list.

        :Parameters:
            router: instance
                subclass of :cls:`wampy.peers.routers.Router`
            realm : string
            topics : list of strings
            message_handler : func
            roles: dictionary

        """
        self.id = str(uuid4())
        self.router = router
        self.realm = realm
        self.topics = topics
        self.message_handler = message_handler
        self.roles = roles or {
            'roles': {
                'subscriber': {},
            },
        }
        self.transport = transport

        self.session = session_builder(
            client=self, router=self.router, realm=self.realm,
            transport=self.transport)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def start(self):
        self.session.begin()
        for topic in self.topics:
            subscribe_to_topic(
                session=self.session, topic=topic, handler=self.topic_handler
            )

        logger.info("subscribed to %s", ", ".join(self.topics))

    def stop(self):
        self.session.end()
        self.subscribed = False

    def topic_handler(self, *args, **kwargs):
        logger.info("handling message: (%s, %s)", args, kwargs)
        self.message_handler(*args, **kwargs)
