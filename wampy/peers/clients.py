# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import logging
import os

from wampy.constants import (
    CROSSBAR_DEFAULT, DEFAULT_TIMEOUT, DEFAULT_ROLES,
    DEFAULT_REALM,
)
from wampy.errors import WampProtocolError, WampyError, WampyTimeOutError
from wampy.session import Session
from wampy.messages import Abort, Cancel, Challenge
from wampy.message_handler import MessageHandler
from wampy.peers.routers import Router
from wampy.roles.caller import CallProxy, RpcProxy
from wampy.roles.publisher import PublishProxy
from wampy.transports import WebSocket, SecureWebSocket

logger = logging.getLogger("wampy.clients")


class Client(object):
    """ A WAMP Client for use in Python applications, scripts and shells.
    """

    def __init__(
        self, url=None, cert_path=None,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
        message_handler=None, name=None,
        call_timeout=DEFAULT_TIMEOUT,
        router=None,
    ):
        """ A WAMP Client "Peer".

        WAMP is designed for application code to run within Clients,
        i.e. Peers.

        Peers have the roles Callee, Caller, Publisher, and Subscriber.

        Subclass this base class to implemente the Roles for your application.

        :Parameters:
            url : string
                The URL of the Router Peer.
                This must include protocol, host and port and an optional path,
                e.g. "ws://example.com:8080" or "wss://example.com:8080/ws".
                Note though that "ws" protocol defaults to port 8080, an "wss"
                to 443.
            cert_path : str
                If using ``wss`` protocol, a certificate might be required by
                the Router. If so, provide here.
            realm : str
                The routing namespace to construct the ``Session`` over.
                Defaults to ``realm1``.
            roles : dictionary
                Description of the Roles implemented by the ``Client``.
                Defaults to ``wampy.constants.DEFAULT_ROLES``.
            message_handler : instance
                An instance of ``wampy.message_handler.MessageHandler``, or
                a subclass of. This controls the conversation between the
                two Peers.
            name : string
                Optional name for your ``Client``. Useful for when testing
                your app or for logging.
            call_timeout : integer
                A Caller might want to issue a call and provide a timeout after
                which the call will finish.
                The value should be in seconds.
            router : instance
                An alternative way to connect to a Router rather than ``url``.
                An instance of a Router Peer, e.g.
                ``wampy.peers.routers.Crossbar``
                This is more configurable and powerful, but requires a copy
                of the Router's config file, making this only really useful
                in single host setups or testing.

        """
        if url and router:
            raise WampyError(
                'Both ``url`` and ``router`` decide how your client connects '
                'to the Router, and so only one can be defined on '
                'instantiation. Please choose one or the other.'
            )

        # the endpoint of a WAMP Router
        self.url = url or CROSSBAR_DEFAULT

        # the ``realm`` is the administrive domain to route messages over.
        self.realm = realm
        # the ``roles`` define what Roles (features) the Client can act,
        # but also configure behaviour such as auth
        self.roles = roles
        # a Session is a transient conversation between two Peers - a Client
        # and a Router. Here we model the Peer we are going to connect to.
        self.router = router or Router(url=self.url, cert_path=cert_path)
        # wampy uses a decoupled "messge handler" to process incoming messages.
        # wampy also provides a very adequate default.
        self.message_handler = message_handler or MessageHandler()
        # generally ``name`` is used for debugging and logging only
        self.name = name or self.__class__.__name__
        self.call_timeout = call_timeout

        # this conversation is over a transport. WAMP messages are transmitted
        # as WebSocket messages by default (well, actually... that's because no
        # other transports are supported!)
        if self.router.scheme == "ws":
            self.transport = WebSocket(
                server_url=self.router.url, ipv=self.router.ipv,
            )
        elif self.router.scheme == "wss":
            self.transport = SecureWebSocket(
                server_url=self.router.url, ipv=self.router.ipv,
                certificate_path=self.router.certificate,
            )
        else:
            raise WampyError(
                'Network protocl must be "ws" or "wss"'
            )

        self._session = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    @property
    def session(self):
        return self._session

    @property
    def subscription_map(self):
        return self.session.subscription_map

    @property
    def registration_map(self):
        return self.session.registration_map

    @property
    def request_ids(self):
        return self.session.request_ids

    @property
    def is_pinging(self):
        return self.session.connection.is_pinging

    @property
    def call(self):
        return CallProxy(client=self)

    @property
    def rpc(self):
        return RpcProxy(client=self)

    @property
    def publish(self):
        return PublishProxy(client=self)

    def start(self):
        # create a Session repr between ourselves and the Router.
        # pass in out ``MessageHandler`` which will process messages
        # before they are passed back to the client.
        self._session = Session(
            client=self,
            router=self.router,
            transport=self.transport,
            message_handler=self.message_handler,
        )

        # establish the session
        message_obj = self.session.begin()

        # raise if Router aborts handshake or we cannot respond to a
        # Challenge.
        if message_obj.WAMP_CODE == Abort.WAMP_CODE:
            raise WampyError(message_obj.message)

        if message_obj.WAMP_CODE == Challenge.WAMP_CODE:
            if 'WAMPYSECRET' not in os.environ:
                raise WampyError(
                    "Wampy requires a client's secret to be "
                    "in the environment as ``WAMPYSECRET``"
                )

            raise WampyError("Failed to handle CHALLENGE")

        logger.debug(
            'client %s has established a session with id "%s"',
            self.name, self.session.id
        )

    def stop(self):
        if self.session and self.session.id:
            self.session.end()

        self.transport.disconnect()

    def send_message(self, message):
        self.session.send_message(message)

    def recv_message(self):
        return self.session.recv_message()

    def make_rpc(self, message):
        logger.debug("%s sending message: %s", self.name, message)

        self.session.send_message(message)

        try:
            response = self.session.recv_message()
        except WampProtocolError as wamp_err:
            logger.error(wamp_err)
            raise
        except WampyTimeOutError:
            logger.warning('cancelling Call after wampy timed the Call out')
            cancelation = Cancel(request_id=message.request_id)
            self.session.send_message(cancelation)
            raise
        except Exception as exc:
            logger.warning("rpc failed!!")
            logger.exception(str(exc))
            raise

        return response

    def register_roles(self):
        # over-ride this if you want to customise how your client regisers
        # its Roles
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
                self.session._register_procedure(
                    procedure_name, invocation_policy)

                logger.debug(
                    '%s registered callee "%s"', self.name, procedure_name,
                )

            if hasattr(maybe_role, 'subscriber'):
                topic = maybe_role.topic
                handler_name = maybe_role.handler.__name__
                handler = getattr(self, handler_name)
                self.session._subscribe_to_topic(handler, topic)

                logger.debug(
                    '%s subscribed to topic "%s"', self.name, topic,
                )
