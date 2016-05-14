import eventlet

from . logger import get_logger
from . messages.hello import Hello
from . messages.goodbye import Goodbye
from . messages import MESSAGE_TYPE_MAP
from . messages import Message
from . networking.connections.wamp import WampConnection


eventlet.monkey_patch()


logger = get_logger('wampy.wamp.session')


class Session(object):
    """ A WAMP Session.

    A Session is a transient conversation between two roles attached to a
    Realm and running over a Transport.

    WAMP Sessions are established over a WAMP Connection.

    A WAMP Session is joined to a Realm on a Router.

    """

    def __init__(self, router, client):
        host = router.host
        port = router.port

        connection = WampConnection(host=host, port=port)
        connection.connect()
        assert connection.connected is True

        self.router = router
        self.client = client
        self.connection = connection
        self.id = None
        self.gthread = None

        message_queue = eventlet.Queue(maxsize=1)
        self.listen_on_connection(connection, message_queue)
        self.message_queue = message_queue

    def listen_on_connection(self, connection, message_queue):
        def connection_handler():
            while True:
                try:
                    data = connection.recv()
                    if data:
                        message_queue.put(data)
                except (SystemExit, KeyboardInterrupt):
                    break

        gthread = eventlet.spawn(connection_handler)
        self.gthread = gthread

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

    @property
    def alive(self):
        if self.id and self.gthread.dead is False:
            return True
        return False

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

    def end(self):
        logger.info('"%s" saying GOODBYE', self.client.name)
        message = Goodbye()
        message.construct()
        self.send(message)
        # kill the green thread listenting to messages
        self.gthread.kill()

    def send(self, message):
        logger.info(
            '%s sending "%s" message',
            self.client.name, MESSAGE_TYPE_MAP[message.WAMP_CODE]
        )

        message = message.serialize()
        self.connection.send(str(message))

    def send_and_receive(self, message):
        self.send(message)
        return self.recv()

    def recv(self):
        logger.info(
            '%s waiting to receive a message', self.client.name,
        )

        message = self._wait_for_message()
        logger.info(
            '%s received "%s" message',
            self.client.name, MESSAGE_TYPE_MAP[message[0]]
        )

        return message
