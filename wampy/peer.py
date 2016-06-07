from abc import ABCMeta, abstractproperty, abstractmethod

import eventlet

from . logger import get_logger
from . messages.hello import Hello
from . messages.register import Register
from . mixins import ConnectionMixin, HandleMessageMixin

from . registry import Registry


logger = get_logger('wampy.peers')

eventlet.monkey_patch()


# The messages concerning the WAMP session itself are mandatory for all
# Peers, i.e. a Client MUST implement "HELLO", "ABORT" and "GOODBYE",
# while a Router MUST implement "WELCOME", "ABORT" and "GOODBYE".

class Peer:

    def __init__(self, realm, roles):
        self.realm = realm
        self.roles = roles

    def abort(self):
        pass

    def goodbye(self):
        pass


class RouterInterface(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        """ Return a string identifier for the Router.

        Required for Session management and logging.

        """
    @abstractproperty
    def realms(self):
        """ Return the names of the routing namespaces administered by
        the Router as a list of strings.

        Required because every WAMP connection is connected to a Realm.

        """

    @abstractproperty
    def roles(self):
        """ Return the names of the Roles that the Router implements
        as a list of strings. As a Router, this must be one or both of
        the Broker and Dealer roles.

        """

    @abstractmethod
    def start(self):
        """ Execute the start-up procedures for the Router """

    @abstractmethod
    def stop(self):
        """ Execute the shut-down procedures for the Router """

    @abstractproperty
    def started(self):
        """ Return a boolean """


class ClientInterface(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        """ Return a string identifier for the Client.

        Required for Session management and logging.

        """

    @abstractmethod
    def realm(self):
        """ Returns the name of the Relam that the Client should
        connect to.

        Required because every WAMP Client connection is connected
        to a Realm, whether a Caller or a Callee, and Routing only
        occurs between WAMP Sessions that have joined the same Realm,
        and so this must be declared by the Session.

        """

    @abstractproperty
    def roles(self):
        """ Return the names of the Roles that the Router implements
        as a list of strings. As a Client, this must include any or
        all of :Subscriber, Publisher, Caller, or Callee roles.

        """

    @abstractmethod
    def session(self):
        """ Returns a WAMP Session object.

        See :class:`~session.Session` for implementation details.

        Required because a Client requries a WAMP Session with a
        Router before message exchange with another Client over a
        Realm.

        """

    @abstractmethod
    def hello(self):
        """ Send the HELLO message and return a Session ID.

        """

    @abstractmethod
    def handle_message(self):
        """ Process incoming or outgoing WAMP messages """


class ClientBase(ConnectionMixin, HandleMessageMixin, ClientInterface):

    def __init__(self, name, realm, roles, router=None):
        """ Base class for any WAMP Client.

        The Client must be initialised with a representation of the Router it
        intends to connect to, and with all the knowledge required to begin a
        Session with this Router, i.e. the ``realm`` and intended ``roles``.

        :Paramaters:
            name : string
                An identifier for the Client.

            realm : string
                The Realm on the Router that the Client should connect to.
                Defaults to "realm1".

            roles : dictionary
                A description of the Roles implemented by the Client,
                e.g. ::

                    {
                        'roles': {
                            'subscriber': {},
                            'publisher': {},
                        },
                    }

            router : instance
                An subclass instance of :class:`~RouterBase`. Optional, because
                the Client may be ran as a service.

        :Raises:
            ConnectionError
                When the WAMP connection to the ``router`` failed.
            SessionError
                When the WAMP connection succeeded, but then the WAMP Session
                failed to establish.

        :Returns:
            None

        Once initialised, ``start`` must be called on the Client, which will
        do three things:

            1.  Establish a WAMP connection with the Router, otherwise raise
                a ``ConnectionError``.
            2.  Proceeded to establishe a WAMP Session with the Router,
                otherwise raise a SessionError.
            3.  Register any RPC entrypoints on the client with the Router.

        """
        self.router = router

        self._name = name
        self._realm = realm
        self._roles = roles

        # a WAMP connection will be made with the Router.
        self.connection = None

        # we spawn a green thread to listen for incoming messages
        self.managed_thread = None
        # incoming messages will be consumed from a Queue
        self.message_queue = eventlet.Queue(maxsize=1)
        # once we receieve a WELCOME message from the Router we'll have a
        # session
        self._session = None

    @property
    def name(self):
        return self._name

    @property
    def realm(self):
        return self._realm

    @property
    def roles(self):
        return self._roles

    @property
    def session(self):
        return self._session

    @property
    def running(self):
        has_connection = bool(self.connection) and self.connection.connected
        has_connection_listener = (
            bool(self.managed_thread) and not self.managed_thread.dead
        )
        has_session = bool(self.session)

        return has_connection and has_connection_listener and has_session

    def start(self):
        # kick off the connection and the listener of it
        self._manage_connection()
        # then then the session over the connection
        self.hello()

        def wait_for_session():
            with eventlet.Timeout(5):
                while self.session is None:
                    eventlet.sleep(0)

        wait_for_session()
        self._register_entrypoints()

        logger.info('%s has started up', self.name)

    def stop(self):
        """
        end then session and kill the message handling green thread
        """
        self.managed_thread.kill()
        assert self.managed_thread.dead is True
        self._session = None
        logger.info('%s has stopped', self.name)

    def hello(self):
        message = Hello(self.realm, self.roles)
        message.construct()
        self._send(message)
        logger.info('sent HELLO')

    def _register_entrypoints(self):
        logger.info('registering entrypoints')

        for maybe_rpc_entrypoint in self.__class__.__dict__.values():
            if hasattr(maybe_rpc_entrypoint, 'rpc'):
                entrypoint_name = maybe_rpc_entrypoint.func_name

                message = Register(procedure=entrypoint_name)
                message.construct()
                request_id = message.request_id

                logger.info(
                    'registering entrypoint "%s"', entrypoint_name
                )

                Registry.request_map[request_id] = (
                    self.__class__, entrypoint_name)

                self._send(message)

                # wait for INVOCATION from Dealer
                with eventlet.Timeout(5):
                    while (self.__class__, entrypoint_name) not in \
                            Registry.registration_map.values():
                        eventlet.sleep(0)

        Registry.client_registry[self.name] = self
        logger.info(
            'registered entrypoints for client: "%s"', self.name
        )


class Router(RouterInterface):

    def welcome(self):
        pass
