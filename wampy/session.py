# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os

from wampy.auth import compute_wcs
from wampy.backends import async_adapter
from wampy.errors import (
    ConnectionError, WampyError, WampyTimeOutError,
    WampProtocolError,
)
from wampy.messages import (
    Abort, Authenticate, Cancel, Challenge, Hello, Goodbye, Register,
    Subscribe, Welcome,
)

from wampy.mixins import ParseUrlMixin
from wampy.transports import WebSocket, SecureWebSocket

logger = logging.getLogger('wampy.session')


class Session(ParseUrlMixin):
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

    def __init__(
        self, router_url, message_handler, ipv, cert_path,
        call_timeout, realm, roles, client_name,
    ):
        """ A Session between a Client and a Router.

        The WAMP layer of the internal architecture.

        :Parameters:
            router_url : string
                The URL of the Router Peer.
            message_handler : instance
                An instance of ``wampy.message_handler.MessageHandler``,
                or a subclass of it. Handles incoming WAMP Messages.
            ipv : int
                The Internet Protocol version for the Transport to use

        """
        self.url = router_url
        # decomposes the url, adding new Session instance variables for
        # them, so that the Session can decide on the Transport it needs
        # to use to connect to the Router
        self.parse_url()

        self.message_handler = message_handler
        self.ipv = ipv
        self.cert_path = cert_path
        self.call_timeout = call_timeout
        self.realm = realm
        self.roles = roles
        self.client_name = client_name

        if self.scheme == "ws":
            self.transport = WebSocket(
                server_url=self.url,
                ipv=self.ipv,
            )
        elif self.scheme == "wss":
            self.transport = SecureWebSocket(
                server_url=self.url,
                ipv=self.ipv,
                certificate_path=self.cert_path,
            )
        else:
            raise WampyError(
                'wampy only suppoers network protocol "ws" or "wss"'
            )

        self.connection = self.transport.connect(upgrade=True)

        self.request_ids = {}
        self.subscription_map = {}
        self.registration_map = {}

        self.session_id = None
        # spawn a green thread to listen for incoming messages over
        # a connection and put them on a queue to be processed
        self._managed_thread = None
        # the MessageHandler is responsible for putting messages on
        # to this queue which are then returned to the Client. The
        # queue is shared between the green threads.
        self._message_queue = async_adapter.message_queue
        self._listen()

    @property
    def id(self):
        return self.session_id

    # TODO wrap in HELLO
    def begin(self):
        self._say_hello()
        # wait for the Welcome Message which the MessageHandler returns to
        # the Client via its private message queue
        logger.info("Session requested")

    # TODO wrap in END
    def end(self, goodbye_from):
        self._say_goodbye(goodbye_from=goodbye_from)
        self.connection.disconnect()
        try:
            self._managed_thread.kill()
        except TypeError:
            pass
        self.session_id = None

    def send_message(self, message_obj):
        message = message_obj.message
        self.connection.send(message)

    # TODO: move this to the Client to remove another layer of abstraction?
    def recv_message(self, source_request_id=None, timeout=None):
        # Messages are passed from the MessageHandler to a queue on the
        # Client.
        try:
            message = async_adapter.receive_message(
                timeout=timeout or self.call_timeout,
            )
        except WampProtocolError as wamp_err:
            logger.error(wamp_err)
            raise
        except WampyTimeOutError:
            if source_request_id:
                logger.warning(
                    'cancelling Call after wampy timed the Call out'
                )
                cancelation = Cancel(request_id=source_request_id)
                self.send_message(cancelation)
            raise
        except Exception as exc:
            logger.warning("rpc failed!!")
            logger.exception(str(exc))
            raise

        return message

    def _say_hello(self):
        details = self.roles
        for role, features in details['roles'].items():
            features.setdefault('features', {})
            features['features'].setdefault('call_timeout', True)

        message = Hello(realm=self.realm, details=details)
        self.send_message(message)

        message_obj = self.recv_message()
        # raise if Router aborts handshake or we cannot respond to a
        # Challenge.
        if message_obj.WAMP_CODE == Abort.WAMP_CODE:
            # gracefully shut down the Client and raise
            self.connection.disconnect()
            self._managed_thread.kill()
            raise WampyError(message_obj.message)

        if message_obj.WAMP_CODE == Challenge.WAMP_CODE:
            if 'WAMPYSECRET' not in os.environ:
                raise WampyError(
                    "Wampy requires a client's secret to be "
                    "in the environment as ``WAMPYSECRET``"
                )

            secret = os.environ['WAMPYSECRET']
            if message_obj.auth_method == 'ticket':
                logger.info("proceeding with ticket authentication method")
                message = Authenticate(secret)
            else:
                logger.info("assuming wampcra authentication method")
                challenge_data = message_obj.challenge
                signature = compute_wcs(secret, str(challenge_data))
                message = Authenticate(signature.decode("utf-8"))

            self.send_message(message)
            message_obj = self.recv_message()

            # raise if Router aborts handshake or we cannot respond to a
            # Challenge.
            if message_obj.WAMP_CODE == Abort.WAMP_CODE:
                # gracefully shut down the Client and raise
                self.connection.disconnect()
                self._managed_thread.kill()
                raise WampyError(message_obj.message)
            elif message_obj.WAMP_CODE == Welcome.WAMP_CODE:
                logger.info(
                    "%s has been Authenticated and Welcomed", self.client_name,
                )

    def _say_goodbye(self, goodbye_from):
        logger.info("%s is saying GoodBye", goodbye_from)
        message = Goodbye()
        self.send_message(message)

        message_obj = self.recv_message()
        if message_obj.WAMP_CODE != Goodbye.WAMP_CODE:
            raise WampyError(
                "Expecting a Goodbye from the Router: got a "
                f"{message_obj.WAMP_CODE} instead",
            )

    def _listen(self):
        # listens on the TCP socket connection to Crossbar.
        # Full Frames are always WAMP messages, which are passed to
        # a MessageHandler.
        connection = self.connection

        def connection_handler():
            while True:
                if not self._managed_thread.ready():
                    async_adapter.sleep()

                if (
                    not hasattr(connection, 'closed') or
                    connection.socket.closed
                ):
                    try:
                        frame = connection.receive()
                        if frame:
                            message = frame.payload
                            logger.info("handling %s", message)
                            self.message_handler.handle_message(message)
                    except (
                        SystemExit, KeyboardInterrupt, ConnectionError,
                        WampProtocolError,
                    ):
                        logger.exception("connection has been terminated")
                        break

                else:
                    import pdb
                    pdb.set_trace()
                    # this is likely the parent gthread closing it deliberately
                    logger.warning("connection gthread has closed")
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
        The REGISTERED Message is handled by the MessageHandler.
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
