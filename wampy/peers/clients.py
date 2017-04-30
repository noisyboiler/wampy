import logging
import inspect

from wampy.errors import WampProtocolError
from wampy.session import session_builder
from wampy.messages import MESSAGE_TYPE_MAP
from wampy.messages.handler import MessageHandler
from wampy.messages.register import Register
from wampy.messages.subscribe import Subscribe
from wampy.roles.caller import CallProxy, RpcProxy
from wampy.roles.publisher import PublishProxy

logger = logging.getLogger("wampy.clients")


class Client(object):
    """ A WAMP Client for use in Python applications, scripts and shells.
    """
    DEFAULT_REALM = "realm1"
    DEFAULT_ROLES = {
        'roles': {
            'subscriber': {},
            'publisher': {},
            'callee': {
                'shared_registration': True,
            },
            'caller': {},
        },
    }

    def __init__(
            self, router, roles=None, message_handler=None,
            transport="websocket", use_tls=False,
            name=None,
    ):

        self.roles = roles or self.DEFAULT_ROLES
        # only support one realm per Router, and we implicitly assume that
        # is the one a client is interested in here. this possibly could be
        # improved....
        self.realm = router.realm
        self.message_handler = message_handler or MessageHandler(client=self)

        self.session = session_builder(
            client=self,
            router=router,
            transport=transport,
            use_tls=use_tls,
        )

        self.request_ids = {}

        self.name = name or self.__class__.__name__

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    @property
    def subscription_map(self):
        return self.session.subscription_map

    @property
    def registration_map(self):
        return self.session.registration_map

    def begin_session(self):
        self.session.begin()

    def end_session(self):
        self.session.end()

    def start(self):
        self.begin_session()
        self._register_roles()

    def stop(self):
        self.end_session()

    def send_message(self, message):
        self.session.send_message(message)

    def recv_message(self):
        return self.session.recv_message()

    def send_message_and_wait_for_response(self, message):
        logger.debug("%s sending message: %s", self.name, message)
        self.session.send_message(message)
        return self.session.recv_message()

    def process_message(self, message):
        logger.info(
            "%s processing %s", self.name, MESSAGE_TYPE_MAP[message[0]])
        self.message_handler(message)

    @property
    def call(self):
        return CallProxy(client=self)

    @property
    def rpc(self):
        return RpcProxy(client=self)

    @property
    def publish(self):
        return PublishProxy(client=self)

    def _register_roles(self):
        logger.info("registering roles for: %s", self.name)

        maybe_roles = []
        bases = [b for b in inspect.getmro(self.__class__) if b is not object]

        for base in bases:
            maybe_roles.extend(
                v for v in base.__dict__.values() if
                inspect.isclass(base) and callable(v)
            )

        for maybe_role in maybe_roles:

            if hasattr(maybe_role, 'callee'):
                procedure_name = maybe_role.__name__
                invocation_policy = maybe_role.invocation_policy
                self._register_procedure(procedure_name, invocation_policy)

            if hasattr(maybe_role, 'subscriber'):
                topic = maybe_role.topic
                handler = maybe_role.handler
                self._subscribe_to_topic(topic, handler)

    def _subscribe_to_topic(self, topic, handler):
        subscriber_name = handler.__name__
        message = Subscribe(topic=topic)
        request_id = message.request_id

        try:
            self.session.send_message(message)
        except Exception as exc:
            raise WampProtocolError(
                "failed to subscribe to {}: \"{}\"".format(
                    topic, exc)
            )

        self.request_ids[request_id] = message, subscriber_name

        logger.info(
            '%s subscribed to topic "%s"', self.name, topic,
        )

    def _register_procedure(self, procedure_name, invocation_policy="single"):
        options = {"invoke": invocation_policy}
        message = Register(procedure=procedure_name, options=options)
        request_id = message.request_id

        try:
            self.session.send_message(message)
        except ValueError:
            raise WampProtocolError(
                "failed to register callee: %s", procedure_name
            )

        self.request_ids[request_id] = procedure_name

        logger.info(
            '%s registered callee "%s"', self.name, procedure_name,
        )
