from . constants import DEALER
from . logger import get_logger


logger = get_logger('wampy.registry')


class PeerRegistry(object):
    registry = {}
    registration_map = {}
    request_map = {}
    registered_roles = {}

    @classmethod
    def register_peer(cls, peer_cls):
        peer = peer_cls()

        if DEALER not in cls.registered_roles and peer.role() != DEALER:
            raise Exception('Must first register a Dealer')

        if peer.name in cls.registry:
            logger.warning('peer already registered: "%s"', peer.name)
            return

        cls.registry[peer.name] = peer
        cls.registered_roles[peer.role()] = peer
        peer.start()
