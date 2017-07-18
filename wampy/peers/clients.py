# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import inspect

from wampy.errors import WampProtocolError
from wampy.session import session_builder
from wampy.message_handler import MessageHandler
from wampy.peers.routers import Crossbar
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
            self, router=None, roles=None, message_handler=None,
            transport="websocket", use_tls=False,
            name=None,
    ):

        self.router = router or Crossbar()
        self.roles = roles or self.DEFAULT_ROLES
        # only support one realm per Router, and we implicitly assume that
        # is the one a client is interested in here. this possibly could be
        # improved....
        self.realm = router.realm
        message_handler = message_handler or MessageHandler()

        self.session = session_builder(
            client=self,
            router=self.router,
            transport=transport,
            message_handler=message_handler,
            use_tls=use_tls,
        )

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

    @property
    def request_ids(self):
        return self.session.request_ids

    def begin_session(self):
        self.session.begin()

    def end_session(self):
        self.session.end()

    def start(self):
        self.begin_session()
        self.register_roles()

    def stop(self):
        self.end_session()

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
        except Exception as exc:
            logger.warning("rpc failed!!")
            logger.exception(str(exc))
            raise

        return response

    @property
    def call(self):
        return CallProxy(client=self)

    @property
    def rpc(self):
        return RpcProxy(client=self)

    @property
    def publish(self):
        return PublishProxy(client=self)

    def register_roles(self):
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
                # maybe_role is not bound
                procedure = getattr(self, procedure_name)
                invocation_policy = maybe_role.invocation_policy
                self.session._register_procedure(
                    procedure, invocation_policy)

                logger.info(
                    '%s registered callee "%s"', self.name, procedure_name,
                )

            if hasattr(maybe_role, 'subscriber'):
                topic = maybe_role.topic
                handler_name = maybe_role.handler.__name__
                handler = getattr(self, handler_name)
                self.session._subscribe_to_topic(handler, topic)
                logger.info(
                    '%s subscribed to topic "%s"', self.name, topic,
                )
