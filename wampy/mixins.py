import eventlet

from . exceptions import ConnectionError
from . logger import get_logger
from . messages.yield_ import Yield
from . messages import Message, MESSAGE_TYPE_MAP
from . networking.connections.wamp import WampConnection
from . registry import Registry
from . session import Session


logger = get_logger('wampy.mixins')


class ConnectionMixin(object):
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


class HandleMessageMixin(object):

    # The messages concerning the WAMP session itself are mandatory for all
    # Peers, i.e. a Client MUST implement "HELLO", "ABORT" and "GOODBYE",
    # while a Router MUST implement "WELCOME", "ABORT" and "GOODBYE".

    def hello(self):
        pass

    def welcome(self):
        pass

    def goodbye(self):
        pass

    def abort(self):
        pass

    def handle_message(self, message):
        logger.info('%s handling a message: "%s"', self.name, message)

        wamp_code = message[0]

        if wamp_code == Message.REGISTERED:  # 64
            _, request_id, registration_id = message
            app, func_name = Registry.request_map[request_id]
            Registry.registration_map[registration_id] = app, func_name

            logger.info(
                '%s registered entrypoint "%s" for "%s"',
                self.name, func_name, app.__name__
            )

        elif wamp_code == Message.INVOCATION:  # 68
            logger.info('%s handling invocation', self.name)
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
            logger.info('%s handling goodbye', self.name)
            _, _, response_message = message
            assert response_message == 'wamp.close.normal'

        elif wamp_code == Message.RESULT:  # 50
            logger.info('%s handling a RESULT', self.name)
            _, request_id, data, response_list = message
            response = response_list[0]
            logger.info(
                '%s has result: "%s"', self.name, response
            )
            self.message_queue.put(message)

        elif wamp_code == Message.WELCOME:  # 2
            logger.info('handling WELCOME for %s', self.name)
            _, session_id, _ = message
            self._session = Session(session_id)
            logger.info(
                '%s has the session: "%s"', self.name, self.session.id
            )

        else:
            logger.exception(
                '%s has an unhandled message: "%s"', self.name, wamp_code
            )

        logger.info('handled message for %s', self.name)
