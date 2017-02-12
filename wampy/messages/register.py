import random

from wampy.messages.message import Message


class Register(Message):
    """ A Callee announces the availability of an endpoint implementing
    a procedure with a Dealer by sending a "REGISTER" message.

    Message is of the format
    ``[REGISTER, Request|id, Options|dict, Procedure|uri]``, e.g. ::

        [
            REGISTER, 25349185, {}, "com.myapp.myprocedure1"
        ]

    "Request" is a random, ephemeral ID chosen by the Callee and
    used to correlate the Dealer's response with the request.

    "Options" is a dictionary that allows to provide additional
    registration request details in a extensible way.

    """
    WAMP_CODE = 64

    def __init__(self, procedure, options=None):
        super(Register, self).__init__()

        self.procedure = procedure
        self.options = options or {}
        self.request_id = random.getrandbits(32)
        self.message = [
            Message.REGISTER, self.request_id, self.options,
            self.procedure
        ]
