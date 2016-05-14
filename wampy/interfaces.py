from abc import ABCMeta, abstractproperty, abstractmethod


class Peer(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        """ Return a string identifier for the Peer """

    @abstractproperty
    def config(self):
        """ Return a dictionary configuration for the Peer """

    @abstractproperty
    def role(self):
        """ Return the Role implemented by the Peer as a string """

    @abstractmethod
    def start(self):
        """ Start up procedures for the Peer """

    @abstractmethod
    def stop(self):
        """ Shut down procedures for the Peer """

    @abstractproperty
    def started(self):
        """ Return a boolean """

    @abstractproperty
    def router(self):
        """ Return an instance of the Router that a Session is
        established with """

    @abstractmethod
    def handle_message(self):
        """ Process incoming or outgoing WAMP messages """
