import logging
import types
from functools import partial

from wampy.messages.handler import MessageHandler
from wampy.peers.clients import Client

logger = logging.getLogger(__name__)


class RegisterProcedureDecorator(object):

    def __init__(self, *args, **kwargs):
        self.invocation_policy = kwargs.get("invocation_policy", "single")

    @classmethod
    def decorator(cls, *args, **kwargs):

        def registering_decorator(fn, args, kwargs):
            invocation_policy = kwargs.get("invocation_policy", "single")
            fn.callee = True
            fn.invocation_policy = invocation_policy
            return fn

        if len(args) == 1 and isinstance(args[0], types.FunctionType):
            # usage without arguments to the decorator:
            return registering_decorator(args[0], args=(), kwargs={})
        else:
            # usage with arguments to the decorator:
            return partial(registering_decorator, args=args, kwargs=kwargs)


class CalleeProxy(Client):
    DEFAULT_ROLES = {
        'roles': {
            'callee': {
                'shared_registration': True,
            },
        },
    }

    def __init__(
        self, procedure_names, callback, router,
        roles=None, message_handler=None, name=None,
    ):
        """ Begin a Session that manages RPC registration and invocations
        only.

        Provide a list of functions names to register, and a single callback
        function to handle INVOCATION

        :Parameters:
            router: instance
                subclass of :cls:`wampy.peers.routers.Router`
            realm : string
            procedure_names : list of strings
            callback : func
            roles: dictionary

        """
        if message_handler:
            message_handler = message_handler(client=self)
        else:
            message_handler = MessageHandler(client=self)

        super(CalleeProxy, self).__init__(
            router,
            roles or self.DEFAULT_ROLES,
            message_handler=message_handler,
            name=name,
        )

        self.procedure_names = procedure_names
        self.callback = callback

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def __getattr__(self, name):
        if name in self.procedure_names:
            # normally an explicit app or service client would handle this,
            # but with this client, many procedures are handled by one
            # callback.
            return self.callback

        return getattr(self, name)

    def start(self):
        self.session.begin()
        for procedure_name in self.procedure_names:
            self._register_procedure(procedure_name)

        logger.info(
            "Register message sent for %s", ", ".join(
                self.procedure_names
            )
        )

    def stop(self):
        self.session.end()


callee = RegisterProcedureDecorator.decorator
