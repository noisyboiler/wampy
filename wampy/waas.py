import eventlet

from . constants import DEALER
from . exceptions import ConfigurationError
from . helpers import Singleton
from . logger import get_logger
from . messages import MESSAGE_TYPE_MAP, Message
from . messages.register import Register
from . messages.yield_ import Yield
from . session import Session


logger = get_logger('wampy.wamp.protocol')


class ServiceRunner(object):
    """ A coordinator of WAMP Callee Client applications exposing
    their entrypoints as a service.

    The ``ApplicationRunner`` coordinates Callee WAMP Clients and
    only runs them when they are needed. It will register all the
    entrypoints for each registered Callee and act as a proxy.

    """
    __metaclass__ = Singleton

    client_registry = {}
    registration_map = {}
    request_map = {}

    def __init__(self):
        self.name = "ServiceRunner"
        self.peer = None

    def register_router(self, peer):
        if self.peer is not None:
            raise ConfigurationError(
                'The ``ServiceRunner`` already has a session open with '
                'a router: "{}:{}"'.format(self.peer.name, self.session.id)
            )

        assert peer.role == DEALER
        if not peer.started:
            peer.start()

        self.peer = peer

    def register_client(self, client):
        """ Register a Callee WAMP Client with the ``ApplicationRunner``.

        :Parameters:
            client : instance
                An instance of a class implementing the
                :class:`~interfaces.Peer` interface.

        .. note::
            The ``client`` should implement the ``Callee`` Role, but may
            also implement others, such as `Caller`.

        """
        for maybe_rpc_entrypoint in client.__class__.__dict__.values():
            if hasattr(maybe_rpc_entrypoint, 'rpc'):
                entrypoint_name = maybe_rpc_entrypoint.func_name

                self._register_rpc_entrypoint(client, entrypoint_name)

                # wait for INVOCATION from Dealer
                with eventlet.Timeout(5):
                    while (client.__class__, entrypoint_name) not in \
                            ServiceRunner.registration_map.values():
                        eventlet.sleep(0)

        ServiceRunner.client_registry[client.name] = client

    def start(self):
        peer = self.peer
        session = Session(peer, client=self)
        session.begin()
        self.session = session

        def run():
            while True:
                message = self.session.recv()
                self.handle_message(message)

        eventlet.spawn(run)

    def stop(self):
        if self.peer.started:
            self.peer.stop()

        self.peer = None
        self.client_registry = {}
        self.registration_map = {}
        self.request_map = {}

    def _register_rpc_entrypoint(self, client, entrypoint_name):
        message = Register(procedure=entrypoint_name)
        message.construct()
        request_id = message.request_id

        ServiceRunner.request_map[request_id] = (
            client.__class__, entrypoint_name)

        self.session.send(message)

        # wait for INVOCATION from Dealer
        with eventlet.Timeout(5):
            while (client.__class__, entrypoint_name) not in \
                    ServiceRunner.registration_map.values():
                eventlet.sleep(0)

    def handle_message(self, message):
        wamp_code = message[0]
        logger.info('handling %s', MESSAGE_TYPE_MAP[message[0]])

        if wamp_code == Message.REGISTERED:
            _, request_id, registration_id = message

            try:
                app, func_name = ServiceRunner.request_map[request_id]
            except KeyError:
                import pdb
                pdb.set_trace()

            logger.info(
                'peer runner registered entrypoint "%s" for "%s"',
                func_name, app.__name__
            )
            ServiceRunner.registration_map[registration_id] = app, func_name

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

            peer_cls, procedure_name = ServiceRunner.registration_map[
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


def get_peer_registry():
    service_runner = ServiceRunner()
    return service_runner.client_registry


def get_registered_entrypoints():
    service_runner = ServiceRunner()
    return service_runner.registration_map
