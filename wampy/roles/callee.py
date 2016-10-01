
def register_callee(wrapped):
    def decorator(fn):
        fn.rpc = True
        return fn

    return decorator(wrapped)


rpc = register_callee
