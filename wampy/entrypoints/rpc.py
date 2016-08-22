import logging

from .. errors import ProcedureNotFoundError, WampProtocolError
from .. messages import Message
from .. messages.call import Call

logger = logging.getLogger('wampy.rpc')


class RpcProxy:

    def __init__(self, client):
        self.client = client

    def __getattr__(self, name):
        from .. registry import Registry
        procedures = [v[1] for v in Registry.registration_map.values()]
        if name in procedures:

            def wrapper(*args, **kwargs):
                message = Call(procedure=name, args=args, kwargs=kwargs)
                logger.info(
                    '%s sending message: "%s"', self.client.name, message)
                self.client.send_message(message)
                response = self.client.recv_message()
                wamp_code = response[0]
                if wamp_code != Message.RESULT:
                    raise WampProtocolError(
                        'unexpected message code: "%s"', wamp_code
                    )

                logger.info(
                    '%s got response: "%s"', self.client.name, response)
                results = response[3]
                result = results[0]
                return result

            return wrapper

        raise ProcedureNotFoundError(name)


def register_rpc(wrapped):
    def decorator(fn):
        fn.rpc = True
        return fn

    return decorator(wrapped)


rpc = register_rpc
