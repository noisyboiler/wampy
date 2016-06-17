import types

from . exceptions import ProcedureNotFoundError
from . messages.call import Call


class ResultProxy:

    def __init__(self, result):
        self.result = result

    def __call__(self):
        return self.result


class RpcProxy:

    def __init__(self, client):
        self.client = client

    def __getattr__(self, name):
        from . registry import Registry
        procedures = [v[1] for v in Registry.registration_map.values()]
        if name in procedures:
            message = Call(procedure=name)
            message.construct()
            self.client._send(message)
            response = self.client._recv()
            results = response[3]

            result_proxy = ResultProxy(result=results[0])
            return result_proxy

        raise ProcedureNotFoundError(name)


def register_rpc(*args, **kwargs):
    assert isinstance(args[0], types.FunctionType)
    # don't support (yet) entrypoints taking args and kwargs
    assert len(args) == 1
    assert kwargs == {}

    wrapped = args[0]

    def decorator(fn, *args, **kwargs):
        fn.rpc = True
        return fn

    return decorator(wrapped, args=(), kwargs={})


rpc = register_rpc
