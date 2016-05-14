""" WAMP As A Service

Specifically WAMP Callee clients as a service.

"""
import eventlet

from . constants import DEALER
from . peer import Peer
from . logger import get_logger
from . messages import MESSAGE_TYPE_MAP, Message
from . messages.register import Register
from . messages.yield_ import Yield
from . registry import Registry
from . session import Session


logger = get_logger('wampy.wamp.services')


class ServiceRunner(Peer):
    """ A coordinator of WAMP Callee Client applications exposing
    their entrypoints as a service.

    The ``ServiceRunner`` coordinates Callee WAMP Clients and
    only runs them when they are needed. It will register all the
    entrypoints for each registered Callee and act as a proxy.

    """
    __instance = None

    # simple Singleton pattern to ensure that there is only one
    # service runner with only one router, session and maps.
    def __new__(cls):
        if ServiceRunner.__instance is None:
            ServiceRunner.__instance = object.__new__(cls)
        return ServiceRunner.__instance

    def __init__(self):
        self.gthread = None
        self.session = None
        self._router = None

    @property
    def name(self):
        return "ServiceRunner"

    @property
    def role(self):
        return DEALER

    @property
    def config(self):
        return {}

    @property
    def router(self):
        return self._router

    @property
    def started(self):
        if self.router is None:
            return False
        return self.router.started

    def start(self):
        assert self.router.started

        session = Session(self.router, client=self)
        session.begin()
        self.session = session
        logger.info('%s has the session: "%s"', self.name, self.session.id)

        def run():
            while True:
                message = self.session.recv()
                self.handle_message(message)

        self.gthread = eventlet.spawn(run)
        logger.info('service runner started')

    def stop(self):
        self.session.end()
        self.router.stop()
        self.gthread.kill()

        self._router = None
        self.client_registry = {}
        self.registration_map = {}
        self.request_map = {}
        logger.info('service runner stopped')

    def register_router(self, peer):
        assert peer.role == DEALER
        assert peer.started

        self._router = peer

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

                self.session.send(message)

                # wait for INVOCATION from Dealer
                with eventlet.Timeout(5):
                    while (client.__class__, entrypoint_name) not in \
                            Registry.registration_map.values():
                        eventlet.sleep(0)

        Registry.client_registry[client.name] = client
        logger.info('%s has registered client: "%s"', self.name, client.name)

    def handle_message(self, message):
        wamp_code = message[0]
        logger.info('handling %s', MESSAGE_TYPE_MAP[message[0]])

        if wamp_code == Message.REGISTERED:
            _, request_id, registration_id = message

            app, func_name = Registry.request_map[request_id]

            logger.info(
                'service runner registered entrypoint "%s" for "%s"',
                func_name, app.__name__
            )
            Registry.registration_map[registration_id] = app, func_name

        elif wamp_code == Message.INVOCATION:
            logger.info(
                'received INVOCATION message from Dealer'
            )

            if len(message) == 4:
                # no call args or kwargs
                _, request_id, registration_id, details = message
            elif len(message) == 5:
                # call args
                raise RuntimeError('unsupported message')
            elif len(message) == 6:
                # call args and kwargs
                raise RuntimeError('unsupported message')

            peer_cls, procedure_name = Registry.registration_map[
                registration_id]

            peer = peer_cls()
            entrypoint = getattr(peer, procedure_name)
            resp = entrypoint()
            result_args = [resp]

            message = Yield(request_id, result_args=result_args)
            message.construct()
            self.session.send(message)
            logger.info('%s sent YIELD message', peer.name)


def register_client(client):
    service_runner = ServiceRunner()
    service_runner.register_client(client)
