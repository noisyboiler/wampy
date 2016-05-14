import eventlet

from . logger import get_logger
from . messages.register import Register
from . registry import Registry
from . session import Session


logger = get_logger('wampy.mixins')


class ClientMixin:

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

        self.session = Session(self.router, client=self)
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
