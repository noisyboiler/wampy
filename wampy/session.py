import eventlet

from . constants import DEFAULT_REALM, DEFAULT_ROLES
from . exceptions import WampProtocolError
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

    def __init__(
            self, name, connection, realm=DEFAULT_REALM, roles=DEFAULT_ROLES):

        if not isinstance(connection, WampConnection):
            raise WampProtocolError(
                'Not a valid connection for a WAMP Session'
            )

        assert connection.connected is True

        self.session_id = None

        message_queue = eventlet.Queue(maxsize=1)
        listen_on_connection(connection, message_queue)

        self.connection = connection
        self.message_queue = message_queue
        self.name = name
        self.realm = realm
        self.roles = roles

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
        message = Hello(self.realm, self.roles)
        message.construct()

        response_message = self.send_and_receive(message)
        welcome_or_challenge, session_id, dealer_roles = response_message

        if welcome_or_challenge != Message.WELCOME:
            raise Exception('Not welcomed by dealer')

        self.session_id = session_id
        self.dealer_roles = dealer_roles

        logger.info('session started for "{}" with ID: {}'.format(
            self.name, self.session_id))

    def send(self, message):
        logger.info(
            'sending "%s" message for "%s"',
            MESSAGE_TYPE_MAP[message.WAMP_CODE], self.name
        )

        if not message.serialized:
            message = message.serialize()

        self.connection.send(message)

    def send_and_receive(self, message):
        self.send(message)
        return self.recv()

    def recv(self):
        message = self._wait_for_message()
        logger.info(
            'received "%s" message for "%s"',
            MESSAGE_TYPE_MAP[message[0]], self.name
        )

        return message
