import logging
import types
from functools import partial

from wampy.messages.register import Register


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


rpc = RegisterProcedureDecorator.decorator
register_rpc = RegisterProcedureDecorator.decorator
