import logging

import eventlet

from wampy.errors import ConnectionError, WampError, WampProtocolError
from wampy.messages import Message, MESSAGE_TYPE_MAP
from wampy.messages.goodbye import Goodbye
from wampy.messages.register import Register
from wampy.messages.subscribe import Subscribe
from wampy.messages.yield_ import Yield
from wampy.messages.hello import Hello
from wampy.networking.connection import WampConnection
from wampy.session import Session


class ClientBase(object):

    def __init__(self):
        self.subscription_map = {}
        self.registration_map = {}

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
            'wampy.peers.clients.{}'.format(self.name.replace(' ', '-')))
        self.logger.info('New client: "%s"', self.name)

    def start(self):
        # kick off the (managed) connection
        self._connect_to_router()
        # then statt a session
        self._say_hello_to_router()
        # and register any user defined roles
        self._register_roles()

        self.logger.info('%s has started', self.name)

    def stop(self):
        self._say_goodbye_to_router()
        message = self._wait_for_message()
        if message[0] != Message.GOODBYE:
            raise WampProtocolError(
                "Unexpected response from router following GOODBYE: {}".format(
                    message
                )
            )

        self.managed_thread.kill()
        self.session = None
        self.subscription_map = {}
        self.logger.info('%s has stopped', self.name)

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
        response = self._send_message_and_wait_for_response(message)

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
        self._send_message(message)

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

    def _register_roles(self):
        maybe_roles = self.__class__.__dict__.values()

        for base in self.__class__.__bases__:
            maybe_roles.extend(base.__dict__.values())

        for maybe_role in maybe_roles:

            if hasattr(maybe_role, 'callee'):
                procedure_name = maybe_role.func_name
                invocation_policy = maybe_role.invocation_policy
                self._register_procedure(procedure_name, invocation_policy)

            if hasattr(maybe_role, 'subscriber'):
                topic = maybe_role.topic
                handler = maybe_role.handler
                self._subscribe(topic, handler)

        roles = self.subscription_map.keys() + self.registration_map.keys()
        if roles:
            self.logger.info(
                'registered additional roles for %s: "%s"',
                self.name, ','.join(roles)
            )

    def _register_procedure(self, procedure_name, invocation_policy="single"):
        self.logger.info(
            "registering %s with invocation policy %s",
            procedure_name, invocation_policy
        )

        options = {"invoke": invocation_policy}
        message = Register(procedure=procedure_name, options=options)

        response_msg = self._send_message_and_wait_for_response(message)
        _, _, registration_id = response_msg

        self.registration_map[procedure_name] = registration_id

        self.logger.info(
            'registering entrypoint "%s" for callee "%s"',
            procedure_name, self.name
        )

    def _subscribe(self, topic, handler):
        procedure_name = handler.func_name
        message = Subscribe(topic=topic)

        response_msg = self._send_message_and_wait_for_response(message)
        _, _, subscription_id = response_msg

        self.subscription_map[procedure_name] = subscription_id, topic

        self.logger.info(
            'registering entrypoint "%s (%s)" for subscriber "%s"',
            procedure_name, topic, self.name
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
            self._send_message(message)

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

    def _recv_message(self):
        self.logger.info(
            '%s waiting to receive a message', self.name,
        )

        message = self._wait_for_message()

        self.logger.info(
            '%s received "%s" message',
            self.name, MESSAGE_TYPE_MAP[message[0]]
        )

        return message

    def _send_message_and_wait_for_response(self, message):
        self._send_message(message)
        return self._recv_message()

    def _send_message(self, message):
        message_type = MESSAGE_TYPE_MAP[message.WAMP_CODE]
        message = message.serialize()

        self.logger.info(
            '%s sending "%s" message: %s',
            self.name, message_type, message
        )

        self._connection.send_websocket_frame(str(message))
