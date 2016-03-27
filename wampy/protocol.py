import eventlet

from . exceptions import MessageRouterConnectionError
from . helpers import Singleton
from . logger import get_logger
from . messages import MESSAGE_TYPE_MAP, Message
from . messages.yield_ import Yield
from . registry import PeerRegistry
from . session import Session


logger = get_logger('wampy.wamp.implementation')


class WampRunner(object):
    __metaclass__ = Singleton

    def __init__(self):
        session = Session(name="WAMP Message Listener")

        no_session = True
        with eventlet.Timeout(5):
            while no_session:
                try:
                    session.begin()
                except MessageRouterConnectionError:
                    continue
                no_session = False

        self.session = session
        self.listen()

    @classmethod
    def start(cls):
        cls()

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
            app, func_name = PeerRegistry.request_map[request_id]
            logger.info(
                'peer runner registered entrypoint "%s" for "%s"',
                func_name, app.__name__
            )
            PeerRegistry.registration_map[registration_id] = app, func_name

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

            peer_cls, procedure_name = PeerRegistry.registration_map[
                registration_id]

            peer = peer_cls()
            entrypoint = getattr(peer, procedure_name)
            resp = entrypoint()
            result_args = [resp]

            message = Yield(request_id, result_args=result_args)
            message.construct()
            self.session.send(message)
            logger.info('%s sent YIELD message', peer.name)
