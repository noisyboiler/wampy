from . peer import Peer
from . mixins import ClientMixin


class Broker(Peer):
    pass


class Dealer(Peer):
    pass


class Caller(ClientMixin, Peer):
    pass


class Callee(ClientMixin, Peer):
    pass


class Publisher(ClientMixin, Peer):
    pass


class Subscriber(ClientMixin, Peer):
    pass
