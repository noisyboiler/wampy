import logging

import eventlet

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.errors import ConnectionError, WampError
from wampy.networking.connection import WampConnection
from wampy.messages.register import Register
from wampy.messages import Message, MESSAGE_TYPE_MAP
from wampy.messages.subscribe import Subscribe
from wampy.messages.goodbye import Goodbye
from wampy.messages.yield_ import Yield
from wampy.messages.hello import Hello
from wampy.roles.publisher import PublishProxy
from wampy.roles.caller import CallProxy, RpcProxy
from wampy.session import Session


class Peer(object):

    def __init__(
            self, name,
            host=DEFAULT_HOST, port=DEFAULT_PORT,
            realm=DEFAULT_REALM, roles=DEFAULT_ROLES
    ):
        """ Base class for any WAMP Client.

        :Paramaters:
            name : string
                An identifier for the Client.

            host : string
                The hostnmae or IP of the Router to connect to. Defaults
                to "localhost".

            port : int
                The port on the Router to connect to. Defaults to 8080.

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

        Once initialised, ``start`` must be called on the Client, which will
        do three things:

            1.  Establish a WAMP connection with the Router, otherwise raise
                a ``ConnectionError``.
            2.  Proceeded to establishe a WAMP Session with the Router,
                otherwise raise a SessionError.
            3.  Register any RPC entrypoints on the client with the Router.

        """
        self.subscription_map = {}
        self.registration_map = {}

        # an identifier of the Client for introspection and logging
        self.name = name or self.__class__.__name__

        self.host = host
        self.port = port
        self.realm = realm
        self.roles = roles

        # a WAMP connection will be made with the Router.
        self._connection = None
        # we spawn a green thread to listen for incoming messages
        self._managed_thread = None
        # incoming messages will be consumed from a Queue
        self._message_queue = eventlet.Queue(maxsize=1)
        # once we receieve a WELCOME message from the Router we'll have a
        # session
        self.session = None

        self.logger = logging.getLogger(
            'wampy.peers.client.{}'.format(self.name.replace(' ', '-')))
        self.logger.info('New client: "%s"', self.name)

    @property
    def call(self):
        return CallProxy(client=self)

    @property
    def rpc(self):
        return RpcProxy(client=self)

    @property
    def publish(self):
        return PublishProxy(client=self)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def _connect_to_router(self):
        connection = WampConnection(
            host=self.host, port=self.port
        )

        self.logger.info(
            '%s connecting to %s', self.host, self.port
        )

        try:
            connection.connect()
        except Exception as exc:
            raise ConnectionError(exc)

        self._listen_on_connection(connection, self._message_queue)
        self._connection = connection

    def _say_hello_to_router(self):
        message = Hello(self.realm, self.roles)
        response = self.send_message_and_wait_for_response(message)

        # response message must be either WELCOME or ABORT
        message_code = response[0]
        if message_code not in [Message.WELCOME, Message.ABORT]:
            raise WampError(
                'unexpected response from HELLO message: {}'.format(
                    response
                )
            )

        return response

    def _say_goodbye_to_router(self):
        message = Goodbye()
        self.send_message(message)

    def _listen_on_connection(self, connection, message_queue):
        def connection_handler():
            while True:
                try:
                    frame = connection.read_websocket_frame()
                    if frame:
                        message = frame.payload
                        self._handle_message(message)
                except (SystemExit, KeyboardInterrupt):
                    break

        gthread = eventlet.spawn(connection_handler)
        self.managed_thread = gthread

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

        for maybe_entrypoint in self.__class__.__dict__.values():
            if hasattr(maybe_entrypoint, 'rpc'):
                entrypoint_name = maybe_entrypoint.func_name
                message = Register(procedure=entrypoint_name)

                response_msg = self.send_message_and_wait_for_response(message)
                _, _, registration_id = response_msg

                self.registration_map[entrypoint_name] = registration_id

                self.logger.info(
                    'registering entrypoint "%s" for callee "%s"',
                    entrypoint_name, self.name
                )

            if hasattr(maybe_entrypoint, 'subscriber'):
                topic = maybe_entrypoint.topic
                handler = maybe_entrypoint.handler
                entrypoint_name = handler.func_name
                message = Subscribe(topic=topic)

                response_msg = self.send_message_and_wait_for_response(message)
                _, _, subscription_id = response_msg

                self.subscription_map[entrypoint_name] = subscription_id, topic

                self.logger.info(
                    'registering entrypoint "%s (%s)" for subscriber "%s"',
                    entrypoint_name, topic, self.name
                )

        self.logger.info(
            'registered entrypoints for client: "%s"', self.name
        )

    def _handle_message(self, message):
        self.logger.info('%s handling a new message', self.name)

        wamp_code = message[0]
        if wamp_code == Message.REGISTERED:  # 64
            self._message_queue.put(message)

        elif wamp_code == Message.INVOCATION:  # 68
            self.logger.info('%s handling invocation', self.name)

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

            entrypoint = getattr(self, procedure_name)
            resp = entrypoint(*args, **kwargs)
            result_args = [resp]

            message = Yield(request_id, result_args=result_args)
            self.send_message(message)

        elif wamp_code == Message.GOODBYE:  # 6
            self.logger.info('%s handling goodbye', self.name)
            _, _, response_message = message
            assert response_message == 'wamp.close.normal'
            self._message_queue.put(message)

        elif wamp_code == Message.RESULT:  # 50
            self.logger.info('%s handling a RESULT', self.name)
            _, request_id, data, response_list = message
            response = response_list[0]
            self.logger.info(
                '%s has result: "%s"', self.name, response
            )

            # the message must be made available to the client
            self._message_queue.put(message)

        elif wamp_code == Message.WELCOME:  # 2
            self.logger.info('handling WELCOME for %s', self.name)
            _, session_id, _ = message
            self.session = Session(
                client=self, router=self.host, session_id=session_id)
            self.logger.info(
                '%s has the session: "%s"', self.name, self.session.id
            )
            self._message_queue.put(message)

        elif wamp_code == Message.ERROR:
            _, _, _, _, _, errors = message
            self.logger.error(errors)
            self._message_queue.put(message)

        elif wamp_code == Message.SUBSCRIBED:
            self.logger.info(
                '%s has subscribed to a topic: "%s"', self.name, message
            )
            self._message_queue.put(message)

        elif wamp_code == Message.EVENT:
            self.logger.info(
                '%s has recieved an event: "%s"', self.name, message
            )

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

            id_to_func_name_map = {
                v[0]: k for k, v in self.subscription_map.items()
            }

            func_name = id_to_func_name_map[subscription_id]
            entrypoint = getattr(self, func_name)
            entrypoint(*payload_list, **payload_dict)

        else:

            self.logger.warning(
                '%s has an unhandled message: "%s"', self.name, message
            )

        self.logger.info('%s handled message: "%s"', self.name, message)

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
        self._say_goodbye_to_router()
        message = self._wait_for_message()
        assert message[0] == Message.GOODBYE
        self.managed_thread.kill()
        self.session = None
        self.subscription_map = {}
        self.logger.info('%s has stopped', self.name)

    def send_message_and_wait_for_response(self, message):
        self.send_message(message)
        return self.recv_message()

    def send_message(self, message):
        message_type = MESSAGE_TYPE_MAP[message.WAMP_CODE]
        message = message.serialize()

        self.logger.info(
            '%s sending "%s" message: %s',
            self.name, message_type, message
        )

        self._connection.send_websocket_frame(str(message))

    def recv_message(self):
        self.logger.info(
            '%s waiting to receive a message', self.name,
        )

        message = self._wait_for_message()

        self.logger.info(
            '%s received "%s" message',
            self.name, MESSAGE_TYPE_MAP[message[0]]
        )

        return message

    def get_subscription_info(self, subscription_id):
        """ Retrieves information on a particular subscription. """
        return self.call("wamp.subscription.get", subscription_id)

    def get_subscription_list(self):
        """ Retrieves subscription IDs listed according to match
        policies."""
        return self.call("wamp.subscription.list")

    def get_subscription_lookup(self, topic):
        """ Obtains the subscription (if any) managing a topic,
        according to some match policy. """
        return self.call("wamp.subscription.lookup", topic)

    def get_subscription_match(self, topic):
        """ Retrieves a list of IDs of subscriptions matching a topic
        URI, irrespective of match policy. """
        return self.call("wamp.subscription.match", topic)

    def list_subscribers(self, subscription_id):
        """ Retrieves a list of session IDs for sessions currently
        attached to the subscription. """
        return self.call(
            "wamp.subscription.list_subscribers", subscription_id)

    def count_subscribers(self, subscription_id):
        """ Obtains the number of sessions currently attached to the
        subscription. """

        return self.call(
            "wamp.subscription.count_subscribers", subscription_id)

    def get_registration_list(self):
        """ Retrieves registration IDs listed according to match
        policies."""
        return self.call("wamp.registration.list")

    def get_registration_lookup(self, procedure_name):
        """ Obtains the registration (if any) managing a procedure,
        according to some match policy."""
        return self.call("wamp.registration.lookup", procedure_name)

    def get_registration_match(self, procedure_name):
        """ Obtains the registration best matching a given procedure
        URI."""
        return self.call("wamp.registration.match", procedure_name)

    def get_registration(self, registration_id):
        """ Retrieves information on a particular registration. """
        return self.call("wamp.registration.get", registration_id)

    def list_callees(self, registration_id):
        """ Retrieves a list of session IDs for sessions currently
        attached to the registration. """
        return self.call(
            "wamp.registration.list_callees", registration_id)

    def count_callees(self, registration_id):
        """ Obtains the number of sessions currently attached to a
        registration. """
        return self.call(
            "wamp.registration.count_callees", registration_id)
