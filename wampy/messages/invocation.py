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
        self.call_args = call_args or tuple()
        self.call_kwargs = call_kwargs or {}

        self.message = [
            self.WAMP_CODE, self.request_id, self.registration_id,
            self.details, self.call_args, self.call_kwargs,
        ]

        self.session = None
        self.procedure_name = None

    def update_kwargs(self, kwargs):
        pass

    def process(self, client):
        self.session = client.session

        args = self.call_args
        kwargs = self.call_kwargs

        self.procedure_name = client.registration_map[self.registration_id]
        entrypoint = getattr(client, self.procedure_name)

        self.update_kwargs(kwargs)

        try:
            result = entrypoint(*args, **kwargs)
        except Exception as exc:
            logger.exception("error calling: %s", self.procedure_name)
            result = None
            error = str(exc)
        else:
            error = None

        self.handle_result(result, error)

    def handle_result(self, result, error=None):
        result_kwargs = {}

        result_kwargs['error'] = error
        result_kwargs['message'] = result
        result_kwargs['meta'] = {}
        result_kwargs['meta']['procedure_name'] = self.procedure_name
        result_kwargs['meta']['session_id'] = self.session.id

        result_args = [result]

        from wampy.messages import Yield
        yield_message = Yield(
            self.request_id,
            result_args=result_args,
            result_kwargs=result_kwargs,
        )
        logger.info("yielding response: %s", yield_message)
        self.session.send_message(yield_message)


class InvocationWithMeta(Invocation):

    def update_kwargs(self, kwargs):
        kwargs['meta'] = {}
        kwargs['meta']['procedure_name'] = self.procedure_name
        kwargs['meta']['session_id'] = self.session.id
        kwargs['meta']['request_id'] = self.request_id
