import eventlet

from . constants import CALLEE, DEALER
from . exceptions import WampProtocolError
from . helpers import Singleton
from . logger import get_logger
from . messages import MESSAGE_TYPE_MAP, Message
from . messages.register import Register
from . messages.yield_ import Yield
from . session import Session


logger = get_logger('wampy.wamp.protocol')


class WampProtocol(object):
    __metaclass__ = Singleton

    peer_registry = {}
    registration_map = {}
    request_map = {}
    registered_roles = {}

    def register_peer(self, peer_instance):
        peer = peer_instance

        if peer.name in WampProtocol.peer_registry:
            logger.warning('peer already registered: "%s"', peer.name)
            return

        if peer.role == DEALER:
            peer.start()
            session = Session(peer)
            session.begin()
            self.session = session
            self.listen()

        elif peer.role == CALLEE:
            if DEALER not in WampProtocol.registered_roles:
                raise Exception('Must first register a Dealer')

            for maybe_rpc_entrypoint in peer.__class__.__dict__.values():
                if hasattr(maybe_rpc_entrypoint, 'rpc'):
                    entrypoint_name = maybe_rpc_entrypoint.func_name

                    message = Register(procedure=entrypoint_name)
                    message.construct()
                    request_id = message.request_id

                    WampProtocol.request_map[request_id] = (
                        peer.__class__, entrypoint_name)
                    self.send(message)

                    # wait for INVOCATION from Dealer
                    with eventlet.Timeout(5):
                        while (peer.__class__, entrypoint_name) not in \
                                WampProtocol.registration_map.values():
                            eventlet.sleep(0)

        else:
            # this project is work in progress, sorry
            raise WampProtocolError(
                'not implemented yet: "{}"'.format(peer.role)
            )

        WampProtocol.peer_registry[peer.name] = peer
        WampProtocol.registered_roles[peer.role] = peer

    def send(self, msg):
        self.session.send(msg)

    def listen(self):
        def run():
            while True:
                message = self.session.recv()
                self.handle_message(message)

        eventlet.spawn(run)

    def handle_message(self, message):
        wamp_code = message[0]
        logger.info('handling %s', MESSAGE_TYPE_MAP[message[0]])

        if wamp_code == Message.REGISTERED:
            _, request_id, registration_id = message
            app, func_name = WampProtocol.request_map[request_id]
            logger.info(
                'peer runner registered entrypoint "%s" for "%s"',
                func_name, app.__name__
            )
            WampProtocol.registration_map[registration_id] = app, func_name

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

            peer_cls, procedure_name = WampProtocol.registration_map[
                registration_id]

            peer = peer_cls()
            entrypoint = getattr(peer, procedure_name)
            resp = entrypoint()
            result_args = [resp]

            message = Yield(request_id, result_args=result_args)
            message.construct()
            self.session.send(message)
            logger.info('%s sent YIELD message', peer.name)


def register_peer(peer):
    manager = WampProtocol()
    manager.register_peer(peer)


def get_peer_registry():
    manager = WampProtocol()
    return manager.peer_registry


def get_registered_entrypoints():
    manager = WampProtocol()
    return manager.registration_map
