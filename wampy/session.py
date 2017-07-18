# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import socket
from functools import partial

import eventlet

from wampy.errors import (
    ConnectionError, WampError, WampProtocolError, WampyError)
from wampy.messages import Message
from wampy.messages import MESSAGE_TYPE_MAP
from wampy.messages.hello import Hello
from wampy.messages.goodbye import Goodbye
from wampy.messages.register import Register
from wampy.messages.subscribe import Subscribe
from wampy.transports.websocket.connection import (
    WampWebSocket, TLSWampWebSocket)


logger = logging.getLogger('wampy.session')


def session_builder(
        client, router, transport="websocket", use_tls=False,
        message_handler=None, ipv=4
):
    if message_handler is None:
        raise WampyError(
            "A ``MessageHandler`` is needed by each ``Session``"
        )

    if transport == "websocket":
        if use_tls:
            transport = TLSWampWebSocket(router)
        else:
            transport = WampWebSocket(router)
    else:
        raise WampError("transport not supported: {}".format(transport))

    return Session(
        client=client, router=router, transport=transport,
        message_handler=message_handler,
    )


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

        :Parameters:
            client : instance
                An instance of :class:`peers.Client`.
            router : instance
                An instance of :class:`peers.Router`.

        """
        self.client = client
        self.router = router
        self.transport = transport
        self.message_handler = message_handler

        self.request_ids = {}
        self.subscription_map = {}
        self.registration_map = {}

        self.session_id = None
        # spawn a green thread to listen for incoming messages over
        # a connection and put them on a queue to be processed
        self._connection = None
        self._managed_thread = None
        self._message_queue = eventlet.Queue()

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
        return self.router.realm['name']

    @property
    def id(self):
        return self.session_id

    def begin(self):
        self._connect()
        self._say_hello()

    def end(self):
        self._say_goodbye()
        self._disconnet()
        self.subscription_map = {}
        self.registration_map = {}
        self.session_id = None

    def send_message(self, message):
        message_type = MESSAGE_TYPE_MAP[message.WAMP_CODE]
        message = message.serialize()

        if self._connection is None:
            raise WampError("WAMP Connection Not Established")

        logger.debug(
            'sending "%s" message: %s', message_type, message
        )

        self._connection.send_websocket_frame(str(message))

    def recv_message(self, timeout=5):
        try:
            message = self._wait_for_message(timeout)
        except eventlet.Timeout:
            raise WampProtocolError(
                "no message returned (timed-out in {})".format(timeout)
            )

        logger.debug(
            'received message: "{}"'.format(MESSAGE_TYPE_MAP[message[0]])
        )

        return message

    def _connect(self):
        connection = self.transport

        try:
            connection.connect()
        except Exception as exc:
            raise ConnectionError(
                'cannot connect to: "{}": {}'.format(self.transport.url, exc)
            )

        self._listen_on_connection(connection, self._message_queue)
        self._connection = connection

    def _disconnet(self):
        _socket = self.transport.socket

        try:
            _socket.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass

        _socket.close()

        self._managed_thread.kill()
        self._connection = None
        self.session = None

        logger.debug('disconnected from %s', self.host)

    def _say_hello(self):
        message = Hello(self.realm, self.roles)
        self.send_message(message)

    def _say_goodbye(self):
        message = Goodbye(wamp_code=6)
        try:
            self.send_message(message)
        except Exception as exc:
            # we can't be sure what the Exception is here because it will
            # be from the Router implementation
            logger.warning("GOODBYE failed!: %s", exc)
        else:
            try:
                message = self.recv_message(timeout=2)
                if message[0] != Message.GOODBYE:
                    raise WampProtocolError(
                        "Unexpected response from GOODBYE message: {}".format(
                            message
                        )
                    )
            except WampProtocolError:
                # Server already gone away?
                pass

    def _listen_on_connection(self, connection, message_queue):

        def connection_handler():
            while True:
                try:
                    frame = connection.read_websocket_frame()
                    if frame:
                        message = frame.payload
                        handler = partial(
                            self.message_handler.handle_message, message, self
                        )
                        eventlet.spawn(handler)
                except (
                        SystemExit, KeyboardInterrupt, ConnectionError,
                        WampProtocolError,
                ):
                    break

        gthread = eventlet.spawn(connection_handler)
        self._managed_thread = gthread

    def _wait_for_message(self, timeout):
        q = self._message_queue

        with eventlet.Timeout(timeout):
            while q.qsize() == 0:
                # if the expected message is not there, switch context to
                # allow other threads to continue working to fetch it for us
                eventlet.sleep()

        message = q.get()
        return message

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

    def _register_procedure(self, procedure, invocation_policy="single"):
        procedure_name = procedure.__name__
        options = {"invoke": invocation_policy}
        message = Register(procedure=procedure_name, options=options)
        request_id = message.request_id

        try:
            self.send_message(message)
        except ValueError:
            raise WampProtocolError(
                "failed to register callee: %s", procedure_name
            )

        self.request_ids[request_id] = procedure
