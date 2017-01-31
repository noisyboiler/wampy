import logging
import types
from functools import partial
from uuid import uuid4

from wampy.messages.register import Register
from wampy.session import session_builder


logger = logging.getLogger(__name__)


def register_procedure(
        session, procedure_name, invocation_policy="single"):

    logger.info(
        "registering %s with invocation policy %s",
        procedure_name, invocation_policy
    )

    options = {"invoke": invocation_policy}
    message = Register(procedure=procedure_name, options=options)

    session.send_message(message)
    response_msg = session.recv_message()

    try:
        _, _, registration_id = response_msg
    except ValueError:
        logger.error(
            "failed to register callee: %s", response_msg
        )
        return

    session.registration_map[procedure_name] = registration_id

    logger.info(
        'registered procedure name "%s"', procedure_name,
    )


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


class ProcedureRegistrationFactory(object):

    def __init__(
            self, router, realm, procedure_names, callback, roles=None,
    ):
        """ Register a list of functions names as "remote procedures" and
        pipe all invocations of these into the single given proxy ``callback``.

        The callback can then YIELD from the actual Callee method,
        and do anything else that it wants to in between.

        .. note::
            The only invocation policy supported is "single".

        :Parameters:
            router: instance
                subclass of :cls:`wampy.peers.routers.Router`
            realm : string
            procedure_names : list of strings
            callback : func
            roles: dictionary

        """
        self.id = str(uuid4())
        self.router = router
        self.realm = realm
        self.procedure_names = procedure_names
        self.callback = callback
        self.roles = roles or {
            'roles': {
                'callee': {
                    'shared_registration': True,
                },
            },
        }

        self.session = session_builder(
            client=self, router=self.router, realm=self.realm
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def __getattr__(self, name):
        if name in self.procedure_names:
            return self.callback

    def start(self):
        self.session.begin()
        for procedure_name in self.procedure_names:
            register_procedure(self.session, procedure_name)

        logger.info("registered to %s", ", ".join(self.procedure_names))

    def stop(self):
        self.session.end()


rpc = RegisterProcedureDecorator.decorator
register_rpc = RegisterProcedureDecorator.decorator
