import types
from abc import ABCMeta, abstractproperty, abstractmethod


class Peer(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def role(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @classmethod
    def register_rpc(cls, *args, **kwargs):
        assert isinstance(args[0], types.FunctionType)
        # don't support (yet) entrypoints taking args and kwargs
        assert len(args) == 1
        assert kwargs == {}

        wrapped = args[0]

        def decorator(fn, *args, **kwargs):
            fn.rpc = True
            return fn

        return decorator(wrapped, args=(), kwargs={})


rpc = Peer.register_rpc
