from abc import ABCMeta, abstractproperty, abstractmethod


class ClientInterface(object):
    """ An actor in a WAMP protocol exchange.

    """

    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        """ Return a string identifier for the Peer.

        Required for Session management and logging.

        """

    @abstractproperty
    def realm(self):
        """ Return the name of the routing namespaces for the Peer to
        attach to.

        Required by the WAMP Session.

        """

    @abstractproperty
    def roles(self):
        """ Return the names of the Roles that the Peer implements
        as a list of strings.

        As a Router, this must be one or both of the Broker and Dealer
        roles, and as a Client it must be one or both of Caller and
        Callee.

        Required for message handling.

        """

    @abstractmethod
    def session(self):
        """ Returns a WAMP Session object.

        See :class:`~session.Session` for implementation details.

        Required for message exchange.

        """

    @abstractmethod
    def start(self):
        """ Execute the start-up procedures for the Peer """

    @abstractmethod
    def stop(self):
        """ Execute the shut-down procedures for the Peer """
