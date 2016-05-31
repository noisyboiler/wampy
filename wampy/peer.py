from abc import ABCMeta, abstractproperty, abstractmethod

import eventlet

from . constants import DEFAULT_REALM, DEFAULT_ROLES
from . exceptions import ConnectionError, SessionError
from . logger import get_logger
from . messages.hello import Hello
from . messages import Message, MESSAGE_TYPE_MAP
from . networking.connections.wamp import WampConnection
from . mixins import HandleMessageMixin
from . session import Session


logger = get_logger('wampy.peers')


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


class ClientBase(HandleMessageMixin, ClientInterface):

    def __init__(self, name, router, realm=DEFAULT_REALM, roles=DEFAULT_ROLES):
        """ Base class for any WAMP Client.

        The Client must be initialised with a representation of the Router it
        intends to connect to, and with all the knowledge required to begin a
        Session with this Router, i.e. the ``realm`` and intended ``roles``.

        :Paramaters:
            name : string
                An identifier for the Client.

            router : instance
                An subclass instance of :class:`~RouterBase`.

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

        response_message = self._recv()
        welcome_or_challenge, session_id, dealer_roles = response_message
        if welcome_or_challenge != Message.WELCOME:
            raise SessionError('Not welcomed by dealer')

        self._session = Session(session_id)
        logger.info(
            '%s has the session: "%s"', self.name, self.session.id)

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

    def _manage_connection(self):
        connection = WampConnection(
            host=self.router.host, port=self.router.port
        )

        try:
            connection.connect()
            self._listen_on_connection(connection, self.message_queue)
        except Exception as exc:
            raise ConnectionError(exc)

        self.connection = connection

    def _listen_on_connection(self, connection, message_queue):
        def connection_handler():
            while True:
                try:
                    frame = connection.recv()
                    if frame:
                        message = frame.payload
                        self.handle_message(message)
                except (SystemExit, KeyboardInterrupt):
                    break

        gthread = eventlet.spawn(connection_handler)
        self.managed_thread = gthread

    def _send(self, message):
        logger.info(
            '%s sending "%s" message',
            self.name, MESSAGE_TYPE_MAP[message.WAMP_CODE]
        )

        message = message.serialize()
        self.connection.send(str(message))

    def _recv(self):
        logger.info(
            '%s waiting to receive a message', self.name,
        )

        message = self._wait_for_message()

        logger.info(
            '%s received "%s" message',
            self.name, MESSAGE_TYPE_MAP[message[0]]
        )

        return message

    def _wait_for_message(self):
        q = self.message_queue
        while q.qsize() == 0:
            # if the expected message is not there, switch context to
            # allow other threads to continue working to fetch it for us
            eventlet.sleep(0)

        message = q.get()
        return message


class Router(RouterInterface):

    def welcome(self):
        pass
