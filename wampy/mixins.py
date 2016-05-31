import eventlet

from . messages.register import Register
from . messages.yield_ import Yield
from . logger import get_logger
from . messages import Message
from . registry import Registry


logger = get_logger('wampy.mixins')


class ClientMixin(object):

    @property
    def started(self):
        try:
            self.session
        except AttributeError:
            return False

        if self.session.alive and self.gthread.dead is False:
            return True
        return False

    def start(self):
        """
        start a session with a router
        register entrypoints with the router
        """
        if self.started:
            return

        assert self.router.started

        self.session.begin()

        logger.info('%s has the session: "%s"', self.name, self.session.id)

        def run():
            while True:
                message = self.session.recv()
                self.handle_message(message)

        gthread = eventlet.spawn(run)
        self.gthread = gthread

        self.register_entrypoints()

    def stop(self):
        """
        end then session and kill the message handling green thread
        """
        self.session.end()
        assert self.session.gthread.dead is True

        self.gthread.kill()
        assert self.gthread.dead is True
        logger.info('%s has stopped', self.name)

    def register_entrypoints(self):
        logger.info('registering entrypoints')

        for maybe_rpc_entrypoint in self.__class__.__dict__.values():
            if hasattr(maybe_rpc_entrypoint, 'rpc'):
                entrypoint_name = maybe_rpc_entrypoint.func_name

                message = Register(procedure=entrypoint_name)
                message.construct()
                request_id = message.request_id

                logger.info(
                    'registering entrypoint "%s"', entrypoint_name
                )

                Registry.request_map[request_id] = (
                    self.__class__, entrypoint_name)

                self.session.send(message)

                # wait for INVOCATION from Dealer
                with eventlet.Timeout(5):
                    while (self.__class__, entrypoint_name) not in \
                            Registry.registration_map.values():
                        eventlet.sleep(0)

        Registry.client_registry[self.name] = self
        logger.info('registered client: "%s"', self.name)


class HandleMessageMixin:
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
            self.session.send(message)

        elif wamp_code == Message.GOODBYE:  # 6
            logger.info('%s handling goodbye', self.name)
            _, _, response_message = message
            assert response_message == 'wamp.close.normal'

        elif wamp_code == Message.RESULT:  # 50
            logger.info('%s handling a RESULT', self.name)
            _, request_id, data, response_list = message
            response = response_list[0]
            self._results.append(response)

        elif wamp_code == Message.WELCOME:  # 2
            logger.info('handling WELCOME for %s', self.name)
            self.message_queue.put(message)
            # switch back to the main context
            eventlet.sleep(0)

        else:
            logger.exception(
                '%s has an unhandled message: "%s"', self.name, wamp_code
            )
