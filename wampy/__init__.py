from . entrypoints import rpc  # NOQA
from . registry import PeerRegistry


def register_peer(peer):
    PeerRegistry.register_peer(peer)
