import types


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
