from abc import ABCMeta, abstractproperty, abstractmethod


class Peer(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        """ Should return a string identifier for the Peer """

    @abstractproperty
    def config(self):
        """ Should return a dictionary configuration for the Peer """

    @abstractproperty
    def role(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractproperty
    def started(self):
        """ Should return a boolean """
