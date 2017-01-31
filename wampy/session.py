import logging

import eventlet

from wampy.errors import ConnectionError, WampError, WampProtocolError
from wampy.messages import Message
from wampy.messages.hello import Hello
from wampy.messages.goodbye import Goodbye
from wampy.messages.yield_ import Yield
from wampy.transports.websocket.connection import WebSocket

from wampy.messages import MESSAGE_TYPE_MAP


logger = logging.getLogger('wampy.session')


def session_builder(client, router, realm, transport="websocket"):
    if transport == "websocket":
        transport = WebSocket(host=router.host, port=router.port)
        return Session(
            client=client, router=router, realm=realm, transport=transport
        )
    raise WampError("transport not supported: {}".format(transport))


class Session(object):
    """ A transient conversation between two Peers attached to a
    Realm and running over a Transport.

    WAMP Sessions are established over a WAMP Connection which is
    the responsibility of the ``Transport`` object.

    Each wampy ``Session`` manages its own WAMP connection via the
    ``Transport``.

    Once the connection is established, the Session is begun when
    the Realm is joined. This is achieved by sending the HELLO message.

    .. note::
        Routing occurs only between WAMP Sessions that have joined the
        same Realm.

    """

    def __init__(self, client, router, realm, transport):
        """ A Session between a Client and a Router.

        :Parameters:
            client : instance
                An instance of :class:`peers.Client`.
            router : instance
                An instance of :class:`peers.Router`.
            realm : str
                The name of the Realm on the ``router`` to join.
            transport : instance
                An instance of :class:`transports.Transport`.

        """
        self.client = client
        self.router = router
        self.realm = realm
        self.transport = transport

        self.subscription_map = {}
        self.registration_map = {}

        self.session_id = None
        # spawn a green thread to listen for incoming messages over
        # a connection and put them on a queue to be processed
        self._connection = None
        self._managed_thread = None
        self._message_queue = eventlet.Queue()

    @property
    def host(self):
        return self.router.host

    @property
    def port(self):
        return self.router.port

    @property
    def roles(self):
        return self.client.roles

    # backwards (or maybe forwards!) compat
    @property
    def id(self):
        return self.session_id

    def begin(self):
        self._connect()
        self._say_hello()

    def end(self):
        self._say_goodbye()
        self._disconnet()
        self.subscription_map = {}
        self.registration_map = {}
        self.session_id = None

    def send_message(self, message):
        message_type = MESSAGE_TYPE_MAP[message.WAMP_CODE]
        message = message.serialize()

        logger.debug(
            'sending "%s" message: %s', message_type, message
        )

        self._connection.send_websocket_frame(str(message))

    def recv_message(self, timeout=5):
        logger.debug('waiting for message')

        try:
            message = self._wait_for_message(timeout)
        except eventlet.Timeout:
            raise WampProtocolError("no message returned")

        logger.debug(
            'received message: "%s"', MESSAGE_TYPE_MAP[message[0]]
        )

        return message

    def handle_message(self, message):
        logger.info(
            "%s received message: %s",
            self.client.id, MESSAGE_TYPE_MAP[message[0]]
        )

        wamp_code = message[0]
        if wamp_code == Message.REGISTERED:  # 64
            self._message_queue.put(message)

        elif wamp_code == Message.INVOCATION:  # 68
            args = []
            kwargs = {}

            try:
                # no args, no kwargs
                _, request_id, registration_id, details = message
            except ValueError:
                # args, no kwargs
                try:
                    _, request_id, registration_id, details, args = message
                except ValueError:
                    # args and kwargs
                    _, request_id, registration_id, details, args, kwargs = (
                        message)

            registration_id_procedure_name_map = {
                v: k for k, v in self.registration_map.items()
            }

            procedure_name = registration_id_procedure_name_map[
                registration_id]

            entrypoint = getattr(self.client, procedure_name)

            kwargs['error'] = None
            kwargs['_meta'] = {}
            kwargs['_meta']['procedure_name'] = procedure_name
            kwargs['_meta']['session_id'] = self.session_id
            kwargs['_meta']['client_id'] = self.client.id

            try:
                resp = entrypoint(*args, **kwargs)
            except Exception as exc:
                resp = None
                kwargs['error'] = exc

            result_args = [resp]

            message = Yield(
                request_id,
                result_args=result_args,
                result_kwargs=kwargs,
            )
            logger.info("yielding response: %s", message)
            self.send_message(message)

        elif wamp_code == Message.GOODBYE:  # 6
            _, _, response_message = message
            self._message_queue.put(message)

        elif wamp_code == Message.RESULT:  # 50
            self._message_queue.put(message)

        elif wamp_code == Message.WELCOME:  # 2
            _, session_id, _ = message
            self.session_id = session_id
            self._message_queue.put(message)

        elif wamp_code == Message.ERROR:
            _, _, _, _, _, errors = message
            logger.error(errors)
            self._message_queue.put(message)

        elif wamp_code == Message.SUBSCRIBED:
            self._message_queue.put(message)

        elif wamp_code == Message.EVENT:
            payload_list = []
            payload_dict = {}

            try:
                # [
                #   EVENT,
                #   SUBSCRIBED.Subscription|id,
                #   PUBLISHED.Publication|id,
                #   Details|dict,
                #   PUBLISH.Arguments|list,
                #   PUBLISH.ArgumentKw|dict]
                # ]
                _, subscription_id, _, details, payload_list, payload_dict = (
                    message)
            except ValueError:

                try:
                    # [
                    #   EVENT,
                    #   SUBSCRIBED.Subscription|id,
                    #   PUBLISHED.Publication|id,
                    #   Details|dict,
                    #   PUBLISH.Arguments|list,
                    # ]
                    _, subscription_id, _, details, payload_list = message
                except ValueError:
                    # [
                    #   EVENT,
                    #   SUBSCRIBED.Subscription|id,
                    #   PUBLISHED.Publication|id,
                    #   Details|dict,
                    # ]
                    _, subscription_id, _, details = message

            func_name, topic = self.subscription_map[subscription_id]
            try:
                func = getattr(self.client, func_name)
            except AttributeError:
                raise WampError(
                    "Event handler not found: {}".format(func_name)
                )

            payload_dict['_meta'] = {}
            payload_dict['_meta']['topic'] = topic
            payload_dict['_meta']['subscription_id'] = subscription_id

            func(*payload_list, **payload_dict)

        else:
            logger.warning(
                'unhandled message: "%s"', message
            )

    def _connect(self):
        connection = self.transport

        try:
            connection.connect()
        except Exception as exc:
            raise ConnectionError(exc)

        self._listen_on_connection(connection, self._message_queue)
        self._connection = connection

    def _disconnet(self):
        self._managed_thread.kill()
        self._connection = None
        self.session = None

        logger.debug('disconnected from %s', self.host)

    def _say_hello(self):
        message = Hello(self.realm, self.roles)
        self.send_message(message)
        response = self.recv_message()

        # response message must be either WELCOME or ABORT
        wamp_code, session_id, _ = response
        if wamp_code not in [Message.WELCOME, Message.ABORT]:
            raise WampError(
                'unexpected response from HELLO message: {}'.format(
                    response
                )
            )

        self.session_id = session_id
        return response

    def _say_goodbye(self):
        message = Goodbye()
        try:
            self.send_message(message)
        except Exception as exc:
            # we can't be sure what the Exception is here because it will
            # be from the Router implementation
            logger.warning("GOODBYE failed!: %s", exc)
        else:
            try:
                message = self.recv_message(timeout=2)
                if message[0] != Message.GOODBYE:
                    raise WampProtocolError(
                        "Unexpected response from GOODBYE message: {}".format(
                            message
                        )
                    )
            except WampProtocolError:
                # Server already gone away?
                pass

    def _listen_on_connection(self, connection, message_queue):
        def connection_handler():
            while True:
                try:
                    frame = connection.read_websocket_frame()
                    if frame:
                        message = frame.payload
                        self.handle_message(message)
                except (
                        SystemExit, KeyboardInterrupt, ConnectionError,
                        WampProtocolError,
                ):
                    break

        gthread = eventlet.spawn(connection_handler)
        self._managed_thread = gthread

    def _wait_for_message(self, timeout):
        q = self._message_queue

        with eventlet.Timeout(timeout):
            while q.qsize() == 0:
                # if the expected message is not there, switch context to
                # allow other threads to continue working to fetch it for us
                eventlet.sleep()

        message = q.get()
        return message
