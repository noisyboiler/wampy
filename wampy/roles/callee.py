import types
from functools import partial


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
