from . interfaces import Peer
from . mixins import ClientMixin


class Dealer(Peer):
    pass


class Caller(ClientMixin, Peer):
    pass


class Callee(ClientMixin, Peer):
    pass
