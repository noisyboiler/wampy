# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

import gevent
import gevent.queue

from wampy.errors import ConnectionError, WampProtocolError
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

    def __init__(self, client, router, connection, message_handler):
        """ A Session between a Client and a Router.

        :Parameters:
            client : instance
                An instance of :class:`peers.Client`
            router : instance
                An instance of :class:`peers.Router`
            connection : instance
                An instance of ``wampy.transports``.
                Defaults to ``wampy.transports.WebSocket``
            message_handler : instance
                An instance of ``wampy.message_handler.MessageHandler``,
                or a subclass of

        """
        self.client = client
        self.router = router
        self.connection = connection
        self.message_handler = message_handler

        self.request_ids = {}
        self.subscription_map = {}
        self.registration_map = {}

        self.session_id = None
        # spawn a green thread to listen for incoming messages over
        # a connection and put them on a queue to be processed
        self._managed_thread = None
        self._message_queue = gevent.queue.Queue()
        self._listen(self.connection, self._message_queue)

    @property
    def host(self):
        return self.router.host

    @property
    def port(self):
        return self.router.port

    @property
    def roles(self):
        return self.client.roles

    @property
    def realm(self):
        return self.client.realm

    @property
    def id(self):
        return self.session_id

    def begin(self):
        return self._say_hello()

    def end(self):
        self._say_goodbye()
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

    def recv_message(self, timeout=5):
        try:
            message = self._message_queue.get(timeout=timeout)
        except gevent.queue.Empty:
            raise WampProtocolError(
                "no message returned (timed-out in {})".format(timeout)
            )

        logger.debug(
            'received message: "%s" for client "%s"',
            message.name,
            self.client.name,
        )

        return message

    def _say_hello(self):
        message = Hello(self.realm, self.roles)
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
            logger.warning("GOODBYE failed!: %s", exc)
        else:
            try:
                message = self.recv_message(timeout=2)
                if message.WAMP_CODE != Goodbye.WAMP_CODE:
                    raise WampProtocolError(
                        "Unexpected response from GOODBYE message: {}".format(
                            message
                        )
                    )
            except WampProtocolError:
                # Server already gone away?
                pass

    def _listen(self, connection, message_queue):

        def connection_handler():
            while True:
                try:
                    frame = connection.receive()
                    if frame:
                        message = frame.payload
                        gevent.spawn(self.message_handler.handle_message,
                                     message, self.client)
                except (
                        SystemExit, KeyboardInterrupt, ConnectionError,
                        WampProtocolError,
                ):
                    break

        gthread = gevent.spawn(connection_handler)
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
