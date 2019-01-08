# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from wampy.backends import async_adapter
from wampy.errors import ConnectionError, WampyTimeOutError, WampProtocolError
from wampy.messages import MESSAGE_TYPE_MAP
from wampy.messages.hello import Hello
from wampy.messages.goodbye import Goodbye
from wampy.messages.register import Register
from wampy.messages.subscribe import Subscribe

logger = logging.getLogger('wampy.session')


class Session(object):
    """ A transient conversation between two Peers attached to a
    Realm and running over a Transport.

    WAMP Sessions are established over a WAMP Connection which is
    the responsibility of the ``Transport`` object.

    Each wampy ``Session`` manages its own WAMP connection via the
    ``Transport``.

    Once the connection is established, the Session is begun when
    the Realm is joined. This is achieved by sending the HELLO message.

    .. note::
        Routing occurs only between WAMP Sessions that have joined the
        same Realm.

    """

    def __init__(self, client, router, transport, message_handler):
        """ A Session between a Client and a Router.

        The WAMP layer of the internal architecture.

        :Parameters:
            client : instance
                An instance of :class:`peers.Client`
            router : instance
                An instance of :class:`peers.Router`
            transport : instance
                An instance of ``wampy.transports``.
            message_handler : instance
                An instance of ``wampy.message_handler.MessageHandler``,
                or a subclass of it. Handles incoming WAMP Messages.

        """
        self.client = client
        self.router = router
        self.transport = transport
        self.connection = self.transport.connect(upgrade=True)
        self.message_handler = message_handler

        self.request_ids = {}
        self.subscription_map = {}
        self.registration_map = {}

        self.session_id = None
        # spawn a green thread to listen for incoming messages over
        # a connection and put them on a queue to be processed
        self._managed_thread = None
        # the MessageHandler is responsible for putting messages on
        # to this queue.
        self._message_queue = async_adapter.message_queue
        self._listen(self.connection)

    @property
    def host(self):
        return self.router.host

    @property
    def port(self):
        return self.router.port

    @property
    def realm(self):
        return self.client.realm

    @property
    def id(self):
        return self.session_id

    def begin(self):
        return self._say_hello()

    def end(self):
        self.connection.stop_pinging()
        self._say_goodbye()
        self.connection.disconnect()
        self.subscription_map = {}
        self.registration_map = {}
        self.session_id = None
        self._managed_thread.kill()
        self._managed_thread = None

    def send_message(self, message_obj):
        message_type = MESSAGE_TYPE_MAP[message_obj.WAMP_CODE]
        message = message_obj.message

        logger.debug(
            'sending "%s" message: "%s" for client "%s"',
            message_type,
            message,
            self.client.name,
        )

        self.connection.send(message)

    def recv_message(self, timeout=None):
        message = async_adapter.receive_message(
            timeout=timeout or self.client.call_timeout,
        )
        logger.debug(
            'received message: "%s" for client "%s"',
            message.name, self.client.name,
        )
        return message

    def _say_hello(self):
        details = self.client.roles
        for role, features in details['roles'].items():
            features.setdefault('features', {})
            features['features'].setdefault('call_timeout', True)

        message = Hello(realm=self.realm, details=details)
        self.send_message(message)
        response = self.recv_message()
        return response

    def _say_goodbye(self):
        message = Goodbye()
        try:
            self.send_message(message)
        except Exception as exc:
            # we can't be sure what the Exception is here because it will
            # be from the Router implementation
            logger.exception("GOODBYE failed!: %s", exc)
        else:
            try:
                message = self.recv_message(timeout=1)
                if message.WAMP_CODE != Goodbye.WAMP_CODE:
                    raise WampProtocolError(
                        "Unexpected response from GOODBYE message: {}".format(
                            message
                        )
                    )
            except WampyTimeOutError:
                logger.warning('no response to Goodbye.... server gone away?')
            except WampProtocolError as exc:
                logger.exception('failed to say Goodbye')

    def _listen(self, connection):

        def connection_handler():
            while True:
                try:
                    frame = connection.receive()
                    if frame:
                        message = frame.payload
                        async_adapter.spawn(
                            self.message_handler.handle_message,
                            message,
                            self.client
                        )
                except (
                    SystemExit, KeyboardInterrupt, ConnectionError,
                    WampProtocolError,
                ):
                    break

        gthread = async_adapter.spawn(connection_handler)
        self._managed_thread = gthread

    def _subscribe_to_topic(self, handler, topic):
        message = Subscribe(topic=topic)
        request_id = message.request_id

        try:
            self.send_message(message)
        except Exception as exc:
            raise WampProtocolError(
                "failed to subscribe to {}: \"{}\"".format(
                    topic, exc)
            )

        self.request_ids[request_id] = message, handler

    def _register_procedure(self, procedure_name, invocation_policy="single"):
        """ Register a "procedure" on a Client as callable over the Router.
        """
        options = {"invoke": invocation_policy}
        message = Register(procedure=procedure_name, options=options)
        request_id = message.request_id

        try:
            self.send_message(message)
        except ValueError:
            raise WampProtocolError(
                "failed to register callee: %s", procedure_name
            )

        self.request_ids[request_id] = procedure_name
