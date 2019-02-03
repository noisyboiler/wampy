# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import logging

from wampy.constants import (
    CROSSBAR_DEFAULT, DEFAULT_TIMEOUT, DEFAULT_ROLES, DEFAULT_REALM,
)
from wampy.session import Session
from wampy.message_handler import MessageHandler
from wampy.roles.caller import CallProxy, RpcProxy
from wampy.roles.publisher import PublishProxy

logger = logging.getLogger("wampy.clients")


class Client(object):
    """ A WAMP Client for use in Python applications, scripts and shells.
    """

    def __init__(
        self, url=CROSSBAR_DEFAULT, cert_path=None, ipv=4, name=None,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES, call_timeout=DEFAULT_TIMEOUT,
        message_handler_cls=None,
    ):
        """ A WAMP Client "Peer".

        :Parameters:
            url : string
                The URL of the Router Peer.
                This must include protocol, host and port and an optional path,
                e.g. "ws://example.com:8080" or "wss://example.com:8080/ws".
                Note though that "ws" protocol defaults to port 8080, an "wss"
                to 443.
            cert_path : str
                If using ``wss`` protocol, a certificate might be required by
                the Router. If so, provide the path to the certificate here
                which will be used when connecting the Secure WebSocket.
            ipv : int
                The Internet Protocol version. Defaults to 4.
            realm : str
                The routing namespace to construct the ``Session`` over.
                Defaults to ``realm1``.
            roles : dictionary
                Description of the Roles implemented by the ``Client``.
                Defaults to ``wampy.constants.DEFAULT_ROLES``.
            message_handler_cls : Class
                A ``wampy.message_handler.MessageHandler`` class, or
                a subclass of. This implements and provides the required
                actions for the the WAMP messages.
            name : string
                Optional name for your ``Client``. Useful for when testing
                your app or for logging.
            call_timeout : integer
                A Caller might want to issue a call and provide a timeout after
                which the call will finish.
                The value should be in seconds.

        """
        # the endpoint of a WAMP Router
        self.url = url
        # when using Secure WebSockets
        self.cert_path = cert_path
        self.ipv = ipv

        # the ``realm`` is the administrive domain to route messages over.
        self.realm = realm
        # the ``roles`` define what Roles (features) the Client can act,
        # but also configure behaviour such as auth
        self.roles = roles

        # wampy uses a decoupled "messge handler" to process incoming messages.
        # wampy also provides a very adequate default.
        # the Client instance is passed into the handler because Callee's and
        # Subscribers are declared on subclasses of the Client class.
        self.message_handler = (
            message_handler_cls(client=self) if message_handler_cls
            else MessageHandler(client=self)
        )

        # generally ``name`` is used for debugging and logging only
        self.name = name or self.__class__.__name__

        # we cannot rely on Routers to implement WAMP call timeout yet.
        # although wampy will send the appropriate instructions in the Call
        # message, we still implement our own cuttoff
        self.call_timeout = call_timeout

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
            router_url=self.url,
            message_handler=self.message_handler,
            ipv=self.ipv,
            cert_path=self.cert_path,
            call_timeout=self.call_timeout,
            realm=self.realm,
            roles=self.roles,
        )

        # establish the session
        self.session.begin()

        logger.info(
            'client %s has established a session with id "%s"',
            self.name, self.session.id
        )

    def stop(self):
        if self.session and self.session.id:
            self.session.end()

        self.session.transport.disconnect()

    def make_rpc(self, message):
        self.session.send_message(message)
        response = self.session.recv_message(
            source_request_id=message.request_id,
        )
        return response

    def register_roles(self):
        # over-ride this if you want to customise how your client registers
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
                    procedure_name, invocation_policy,
                )

                logger.debug(
                    '%s registered callee "%s"', self.name, procedure_name,
                )

            if hasattr(maybe_role, 'subscriber'):
                topic = maybe_role.topic
                handler_name = maybe_role.handler.__name__
                handler = getattr(self, handler_name)
                self.session._subscribe_to_topic(
                    handler, topic,
                )

                logger.debug(
                    '%s subscribed to topic "%s"', self.name, topic,
                )
