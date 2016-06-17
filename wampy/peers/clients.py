import eventlet

from .. logger import get_logger
from .. rpc import RpcProxy

from . bases import ClientBase


class Client(ClientBase):
    """ Represents the "client" side of a WAMP Session.
    """

    def __init__(self, name, realm, roles, router):
        """ Base class for any WAMP Client.

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
                An subclass instance of :class:`~RouterBase`.

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
        self.rpc = RpcProxy(client=self)

        # a WAMP connection will be made with the Router.
        self._connection = None
        # we spawn a green thread to listen for incoming messages
        self._managed_thread = None
        # incoming messages will be consumed from a Queue
        self._message_queue = eventlet.Queue(maxsize=1)
        # once we receieve a WELCOME message from the Router we'll have a
        # session
        self._session = None
        # an identifier of the Client for introspection and logging
        self._name = name
        self._realm = realm
        self._roles = roles

        self.logger = get_logger(
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
        self.logger.info('%s has started', self.name)

    def stop(self):
        self.managed_thread.kill()
        # TODO: say goodbye
        self._session = None
        self.logger.info('%s has stopped', self.name)
