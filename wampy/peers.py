import socket
from abc import ABCMeta, abstractproperty, abstractmethod
from time import time as now

import eventlet

from . exceptions import ConnectionError
from . logger import get_logger
from . messages import Message, MESSAGE_TYPE_MAP
from . messages.hello import Hello
from . messages.register import Register
from . messages.yield_ import Yield
from . networking.connections.tcp import TCPConnection
from . networking.connections.wamp import WampConnection
from . registry import Registry
from . session import Session


eventlet.monkey_patch()


class Peer(object):
    """ Models every actor in a WAMP protocol exchange.

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


class ClientBase(Peer):

    def __init__(self):
        # a WAMP connection will be made with the Router.
        self._connection = None
        # we spawn a green thread to listen for incoming messages
        self._managed_thread = None
        # incoming messages will be consumed from a Queue
        self._message_queue = eventlet.Queue(maxsize=1)
        # once we receieve a WELCOME message from the Router we'll have a
        # session
        self._session = None

    def _connect_to_router(self):
        connection = WampConnection(
            host=self.router.host, port=self.router.port
        )

        try:
            connection.connect()
            self._listen_on_connection(connection, self._message_queue)
        except Exception as exc:
            raise ConnectionError(exc)

        self._connection = connection

    def _say_hello_to_router(self):
        message = Hello(self.realm, self.roles)
        message.construct()
        self._send(message)
        self.logger.info('sent HELLO')

    def _listen_on_connection(self, connection, message_queue):
        def connection_handler():
            while True:
                try:
                    frame = connection.recv()
                    if frame:
                        message = frame.payload
                        self._handle_message(message)
                except (SystemExit, KeyboardInterrupt):
                    break

        gthread = eventlet.spawn(connection_handler)
        self.managed_thread = gthread

    def _send(self, message):
        self.logger.info(
            '%s sending "%s" message',
            self.name, MESSAGE_TYPE_MAP[message.WAMP_CODE]
        )

        message = message.serialize()
        self._connection.send(str(message))

    def _recv(self):
        self.logger.info(
            '%s waiting to receive a message', self.name,
        )

        message = self._wait_for_message()

        self.logger.info(
            '%s received "%s" message',
            self.name, MESSAGE_TYPE_MAP[message[0]]
        )

        return message

    def _wait_for_message(self):
        q = self._message_queue
        while q.qsize() == 0:
            # if the expected message is not there, switch context to
            # allow other threads to continue working to fetch it for us
            eventlet.sleep(0)

        message = q.get()
        return message

    def _register_entrypoints(self):
        self.logger.info('registering entrypoints')

        for maybe_rpc_entrypoint in self.__class__.__dict__.values():
            if hasattr(maybe_rpc_entrypoint, 'rpc'):
                entrypoint_name = maybe_rpc_entrypoint.func_name

                message = Register(procedure=entrypoint_name)
                message.construct()
                request_id = message.request_id

                self.logger.info(
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
        self.logger.info(
            'registered entrypoints for client: "%s"', self.name
        )

    def _handle_message(self, message):
        self.logger.info('%s handling a message: "%s"', self.name, message)

        wamp_code = message[0]

        if wamp_code == Message.REGISTERED:  # 64
            _, request_id, registration_id = message
            app, func_name = Registry.request_map[request_id]
            Registry.registration_map[registration_id] = app, func_name

            self.logger.info(
                '%s registered entrypoint "%s" for "%s"',
                self.name, func_name, app.__name__
            )

        elif wamp_code == Message.INVOCATION:  # 68
            self.logger.info('%s handling invocation', self.name)
            _, request_id, registration_id, details = message

            _, procedure_name = Registry.registration_map[
                registration_id]

            entrypoint = getattr(self, procedure_name)
            resp = entrypoint()
            result_args = [resp]

            message = Yield(request_id, result_args=result_args)
            message.construct()
            self._send(message)

        elif wamp_code == Message.GOODBYE:  # 6
            self.logger.info('%s handling goodbye', self.name)
            _, _, response_message = message
            assert response_message == 'wamp.close.normal'

        elif wamp_code == Message.RESULT:  # 50
            self.logger.info('%s handling a RESULT', self.name)
            _, request_id, data, response_list = message
            response = response_list[0]
            self.logger.info(
                '%s has result: "%s"', self.name, response
            )
            self._message_queue.put(message)

        elif wamp_code == Message.WELCOME:  # 2
            self.logger.info('handling WELCOME for %s', self.name)
            _, session_id, _ = message
            self._session = Session(
                client=self, router=self.router, session_id=session_id)
            self.logger.info(
                '%s has the session: "%s"', self.name, self.session.id
            )

        else:
            self.logger.warning(
                '%s has an unhandled message: "%s"', self.name, wamp_code
            )


class RouterBase(Peer):

    def __init__(self):
        pass

    def _wait_until_ready(self, timeout=7, raise_if_not_ready=True):
        self.logger.info('create TCPConnection')
        # we're only ready when it's possible to connect to the router
        # over TCP - so let's just try it.
        connection = TCPConnection(host=self.host, port=self.port)
        end = now() + timeout

        ready = False
        self.logger.info('wait until ready')

        while not ready:
            timeout = end - now()
            if timeout < 0:
                if raise_if_not_ready:
                    self.logger.exception('%s unable to connect', self.name)
                    raise ConnectionError(
                        'Failed to connect to router'
                    )
                else:
                    return ready

            try:
                connection.connect()
            except socket.error:
                self.logger.warning('failed to connect')
            else:
                ready = True

        return ready


class Client(ClientBase):
    """ Represents the "client" side of a WAMP Session.

    The client might be a Caller or a Callee, or both, and will
    establish a WAMP Session with a Realm provided by a Router.

    """

    def __init__(self, name, realm, roles, router=None, logger=None):
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
        super(Client, self).__init__()

        self.router = router

        self._name = name
        self._realm = realm
        self._roles = roles

        self.logger = logger or get_logger(
            'wampy.peers.client.{}'.format(name.replace(' ', '-')))
        self.logger.info('New client: "%s"', name)

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

    def start(self):
        # kick off the connection and the listener of it
        self._connect_to_router()
        # then then the session over the connection
        self._say_hello_to_router()

        def wait_for_session():
            with eventlet.Timeout(5):
                while self.session is None:
                    eventlet.sleep(0)

        wait_for_session()
        self._register_entrypoints()

    def stop(self):
        """
        end then session and kill the message handling green thread
        """
        self.managed_thread.kill()
        assert self.managed_thread.dead is True
        self._session = None
        self.logger.info('%s has stopped', self.name)


class Router(RouterBase):
    """ Represents the "router" side of a WAMP Session.

    """

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.logger = get_logger(
            'wampy.peers.router.{}'.format(self.name.replace(' ', '-'))
        )
        self.logger.info('New router: "%s"', self.name)
