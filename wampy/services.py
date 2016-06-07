""" WAMP As A Service

Specifically WAMP Callee clients as a service.

"""
import eventlet

from . constants import DEALER
from . logger import get_logger
from . messages.hello import Hello
from . messages.register import Register
from . mixins import ConnectionMixin, HandleMessageMixin
from . registry import Registry


logger = get_logger('wampy.wamp.services')


class ServiceRunner(ConnectionMixin, HandleMessageMixin):
    """ A coordinator of WAMP Callee Client applications exposing
    their entrypoints as a service.

    The ``ServiceRunner`` coordinates Callee WAMP Clients and
    only runs them when they are needed. It will register all the
    entrypoints for each registered Callee and act as a proxy.

    """

    def __init__(self, router, realm, roles):
        self.router = router
        self.realm = realm
        self.roles = roles

        self._session = None
        self._gthread = None

        # a WAMP connection will be made with the Router.
        self.connection = None

        # we spawn a green thread to listen for incoming messages
        self.managed_thread = None
        # incoming messages will be consumed from a Queue
        self.message_queue = eventlet.Queue(maxsize=1)

    @property
    def name(self):
        return "ServiceRunner"

    @property
    def role(self):
        return DEALER

    @property
    def session(self):
        return self._session

    def start(self):
        # kick off the connection and the listener of it
        self._manage_connection()
        # then then the session over the connection
        self.hello()

        def wait_for_session():
            with eventlet.Timeout(5):
                while self.session is None:
                    eventlet.sleep(0)

        wait_for_session()

        logger.info('%s has started up', self.name)

    def stop(self):
        # kill a green thread
        self.managed_thread.kill()
        assert self.managed_thread.dead is True

        # stop a subprocess
        self.router.stop()

        # reset variables
        self._router = None
        self.client_registry = {}
        self.registration_map = {}
        self.request_map = {}

        logger.info('%s stopped', self.name)

    def hello(self):
        message = Hello(self.realm, self.roles)
        message.construct()
        self._send(message)
        logger.info('sent HELLO')

    def register_client(self, client):
        """ Register a Callee WAMP Client with the ``ServiecRunner``.

        :Parameters:
            client : instance
                An instance of a class implementing the
                :class:`~peer.Peer` interface.

        """
        logger.info('registering entrypoints')

        for maybe_rpc_entrypoint in client.__class__.__dict__.values():
            if hasattr(maybe_rpc_entrypoint, 'rpc'):
                entrypoint_name = maybe_rpc_entrypoint.func_name

                message = Register(procedure=entrypoint_name)
                message.construct()
                request_id = message.request_id

                logger.info(
                    'registering request of entrypoint "%s"', entrypoint_name
                )

                Registry.request_map[request_id] = (
                    client.__class__, entrypoint_name)

                self._send(message)

                # wait for INVOCATION from Dealer
                with eventlet.Timeout(5):
                    while (client.__class__, entrypoint_name) not in \
                            Registry.registration_map.values():
                        eventlet.sleep(0)

        Registry.client_registry[client.name] = client
        logger.info('%s has registered client: "%s"', self.name, client.name)
