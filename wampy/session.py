import eventlet

from . logger import get_logger
from . messages.hello import Hello
from . messages import MESSAGE_TYPE_MAP
from . messages import Message
from . networking.connections.wamp import WampConnection


eventlet.monkey_patch()


logger = get_logger('wampy.wamp.session')


def listen_on_connection(connection, message_queue):
    def connection_handler():
        while True:
            try:
                data = connection.recv()
                if data:
                    message_queue.put(data)
            except (SystemExit, KeyboardInterrupt):
                break

    eventlet.spawn(connection_handler)


class Session(object):
    """ A WAMP Session.

    A Session is a transient conversation between two Peers attached to a
    Realm and running over a Transport.

    WAMP Sessions are established over a WAMP Connection.

    A WAMP Session is joined to a Realm on a Router.

    """

    def __init__(self, router):
        host = router.host
        port = router.port

        connection = WampConnection(host=host, port=port)
        connection.connect()
        assert connection.connected is True

        self.router = router
        self.connection = connection
        self.id = None

        message_queue = eventlet.Queue(maxsize=1)
        listen_on_connection(connection, message_queue)
        self.message_queue = message_queue

    @property
    def realms(self):
        return self.router.config['workers'][0]['realms']

    @property
    def realm(self):
        # ensure our simpilfied world holds true
        assert len(self.realms) == 1
        # then return it
        return self.realms[0]['name']

    @property
    def roles(self):
        realm = self.realm
        roles = realm['roles']
        # ensure our simpilfied world holds true
        assert len(roles) == 1
        # then return it
        return roles[0]

    def _wait_for_message(self):
        # must re-import because of some context-switching namespace
        # confusion!
        import eventlet

        q = self.message_queue
        while q.qsize() == 0:
            # if the expected message is not there, switch context to
            # allow other threads to continue working to fetch it for us
            eventlet.sleep(0)

        frame = q.get()
        message = frame.payload
        return message

    def begin(self):
        DEFAULT_ROLES = {
            'roles': {
                'subscriber': {},
                'publisher': {},
            },
        }
        message = Hello(self.realm, DEFAULT_ROLES)
        message.construct()
        response_message = self.send_and_receive(message)
        welcome_or_challenge, session_id, dealer_roles = response_message

        if welcome_or_challenge != Message.WELCOME:
            raise Exception('Not welcomed by dealer')

        self.id = session_id
        self.dealer_roles = dealer_roles

        logger.info('session started with ID: {}'.format(self.id))

    def send(self, message):
        logger.info(
            'sending "%s" message', MESSAGE_TYPE_MAP[message.WAMP_CODE]
        )

        if not message.serialized:
            message = message.serialize()

        self.connection.send(str(message))

    def send_and_receive(self, message):
        self.send(message)
        return self.recv()

    def recv(self):
        message = self._wait_for_message()
        logger.info(
            'received "%s" message', MESSAGE_TYPE_MAP[message[0]]
        )

        return message
