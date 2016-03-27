import socket

import eventlet

from . constants import DEFAULT_REALM, DEFAULT_ROLES
from . exceptions import MessageRouterConnectionError
from . logger import get_logger
from . messages.hello import Hello
from . messages import MESSAGE_TYPE_MAP
from . messages import Message
from . networking.connections.wamp import WampConnection


eventlet.monkey_patch()

logger = get_logger('wampy.wamp.session')


class Session(object):

    def __init__(
            self, name, realm=DEFAULT_REALM, roles=DEFAULT_ROLES):

        self.name = name
        self.realm = realm
        self.roles = roles

        self.session = None
        # keep a WAMP conection to the router open in the background
        # with a cross-greenlet queue to pass messages to the main thread
        self.connection = WampConnection(host='localhost', port=8080)
        self.message_queue = eventlet.Queue(maxsize=1)

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

    def _connect(self):
        connection = self.connection

        def connection_handler():
            while True:
                try:
                    data = self.connection.recv()
                    if data:
                        self.message_queue.put(data)
                except (SystemExit, KeyboardInterrupt):
                    break

        try:
            connection.connect()
        except socket.error as exc:
            if 'ECONNREFUSED' in str(exc):
                raise MessageRouterConnectionError(
                    'The client cannot connect to a message router - '
                    'is one running? \nEither start one yourself, else '
                    'run Crossbar.io in the background by starting the '
                    'default dealer role using the `setup_roles` '
                    'shortcut (see docs for more help).'
                )

            raise

        eventlet.spawn(connection_handler)

    def begin(self):
        self._connect()
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
