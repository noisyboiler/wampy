import random

from wampy.messages.message import Message


class Call(Message):
    """ When a Caller wishes to call a remote procedure, it sends a "CALL"
    message to a Dealer.

    Message is of the format
    ``[CALL, Request|id, Options|dict, Procedure|uri, Arguments|list,
    ArgumentsKw|dict]``, e.g. ::

        [
            CALL, 10001, {}, "com.myapp.myprocedure1", [], {}
        ]

    "Request" is a random, ephemeral ID chosen by the Callee and
    used to correlate the Dealer's response with the request.

    "Options" is a dictionary that allows to provide additional
    registration request details in a extensible way.

    """
    WAMP_CODE = 48

    def __init__(self, procedure, options=None, args=None, kwargs=None):
        super(Call, self).__init__()

        self.procedure = procedure
        self.options = options or {}
        self.args = args or []
        self.kwargs = kwargs or {}
        self.request_id = random.getrandbits(32)
        self.message = [
            Message.CALL, self.request_id, self.options, self.procedure,
            self.args, self.kwargs
        ]
