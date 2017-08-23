# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from wampy.constants import NOT_AUTHORISED
from wampy.errors import RemoteError, WampProtocolError, NotAuthorisedError
from wampy.messages import Error, Result
from wampy.messages import MESSAGE_TYPE_MAP
from wampy.messages.call import Call

logger = logging.getLogger('wampy.rpc')


class CallProxy:
    """ Proxy wrapper of a `wampy` client for WAMP application RPCs.

    Applictions and their endpoints are identified by dot delimented
    strings, e.g. ::

        "com.example.endpoints"

    and a `CallProxy` object will call such and endpoint, passing in
    any `args` or `kwargs` necessary.

    """
    def __init__(self, client):
        self.client = client

    def __call__(self, procedure, *args, **kwargs):
        message = Call(procedure=procedure, args=args, kwargs=kwargs)
        response = self.client.make_rpc(message)
        wamp_code = response.WAMP_CODE

        if wamp_code == Error.WAMP_CODE:
            logger.error("call returned an error: %s", response)
            return response
        elif wamp_code == Result.WAMP_CODE:
            return response.value

        raise WampProtocolError("unexpected response: %s", response)


class RpcProxy:
    """ Proxy wrapper of a `wampy` client for WAMP application RPCs
    where the endpoint is a non-delimted single string name, such as
    a function name, e.g. ::

        "get_data"

    The typical use case of this proxy class is for microservices
    where endpoints are class methods.

    """
    def __init__(self, client):
        self.client = client

    def __getattr__(self, name):

        def wrapper(*args, **kwargs):
            message = Call(procedure=name, args=args, kwargs=kwargs)
            response = self.client.make_rpc(message)

            wamp_code = response.WAMP_CODE
            if wamp_code == Error.WAMP_CODE:
                _, _, request_id, _, endpoint, exc_args, exc_kwargs = (
                    response.message)

                if endpoint == NOT_AUTHORISED:
                    raise NotAuthorisedError(
                        "{} - {}".format(self.client.name, exc_args[0])
                    )

                raise RemoteError(
                    endpoint, request_id, *exc_args, **exc_kwargs
                )

            if wamp_code != Result.WAMP_CODE:
                raise WampProtocolError(
                    'unexpected message code: "%s (%s) %s"',
                    wamp_code, MESSAGE_TYPE_MAP[wamp_code],
                    response[5]
                )

            result = response.value
            logger.debug("RpcProxy got result: %s", result)
            return result

        return wrapper
