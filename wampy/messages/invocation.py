import logging

from wampy.messages.message import Message

logger = logging.getLogger('wampy.messagehandler')


class Invocation(Message):
    """Actual invocation of an endpoint sent by Dealer to a Callee.

       [INVOCATION, Request|id, REGISTERED.Registration|id,
           Details|dict]

       [INVOCATION, Request|id, REGISTERED.Registration|id,
           Details|dict, C* Arguments|list]

       [INVOCATION, Request|id, REGISTERED.Registration|id,
           Details|dict, CALL.Arguments|list, CALL.ArgumentsKw|dict]

    """

    WAMP_CODE = 68

    def __init__(
            self, wamp_code, request_id, registration_id, details,
            call_args=None, call_kwargs=None,
    ):
        assert wamp_code == self.WAMP_CODE

        self.request_id = request_id
        self.registration_id = registration_id
        self.details = details
        self.call_args = call_args
        self.call_kwargs = call_kwargs

        self.message = [
            self.WAMP_CODE, self.request_id, self.registration_id,
            self.details, self.call_args, self.call_kwargs,
        ]

    def process(self, message, client):
        session = client.session

        args = []
        kwargs = {}

        try:
            # no args, no kwargs
            _, request_id, registration_id, details = message
        except ValueError:
            # args, no kwargs
            try:
                _, request_id, registration_id, details, args = message
            except ValueError:
                # args and kwargs
                _, request_id, registration_id, details, args, kwargs = (
                    message)

        registration_id_procedure_name_map = {
            v: k for k, v in session.registration_map.items()
        }

        procedure_name = registration_id_procedure_name_map[
            registration_id]

        entrypoint = getattr(client, procedure_name)

        try:
            resp = entrypoint(*args, **kwargs)
        except Exception as exc:
            resp = None
            error = str(exc)
        else:
            error = None

        result_kwargs = {}

        result_kwargs['error'] = error
        result_kwargs['message'] = resp
        result_kwargs['meta'] = {}
        result_kwargs['meta']['procedure_name'] = procedure_name
        result_kwargs['meta']['session_id'] = session.id
        result_kwargs['meta']['client_id'] = client.id

        result_args = [resp]

        from wampy.messages import Yield
        yield_message = Yield(
            request_id,
            result_args=result_args,
            result_kwargs=result_kwargs,
        )
        logger.info("yielding response: %s", yield_message)
        session.send_message(yield_message)
