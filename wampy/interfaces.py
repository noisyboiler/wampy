from abc import ABCMeta, abstractproperty, abstractmethod


class Peer(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def config(self):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def role(self):
        pass

    @abstractmethod
    def start(self):
        pass
