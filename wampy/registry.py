from . constants import DEALER
from . logger import get_logger


logger = get_logger('wampy.registry')


class PeerRegistry(object):
    config_registry = {}
    peer_registry = {}
    registration_map = {}
    request_map = {}
    registered_roles = {}

    @classmethod
    def register_peer(cls, peer_instance, peer_configuration=None):
        peer = peer_instance

        if DEALER not in cls.registered_roles and peer.role != DEALER:
            raise Exception('Must first register a Dealer')

        if peer.name in cls.peer_registry:
            logger.warning('peer already registered: "%s"', peer.name)
            return

        cls.peer_registry[peer.name] = peer
        cls.config_registry[peer.name] = peer_configuration
        cls.registered_roles[peer.role] = peer

        peer.start()

    @classmethod
    def register_peers_from_config(cls, abs_path_to_config):
        """ Register multiple Peers from a YAML configuration file """
