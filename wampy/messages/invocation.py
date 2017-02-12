from wampy.messages.message import Message


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

    def process(self, message):
        pass
