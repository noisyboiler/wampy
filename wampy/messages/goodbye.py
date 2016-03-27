from . import Message


class Goodbye(Message):
    """ Send a GOODBYE message to the Router.

    Message is of the format ``[GOODBYE, Details|dict, Reason|uri]``, e.g. ::

        [
            GOODBYE, {}, "wamp.close.normal"
        ]

    """
    WAMP_CODE = 6
    DEFAULT_REASON = "wamp.close.normal"

    def __init__(self, reason=DEFAULT_REASON, message=None):
        super(Goodbye, self).__init__()

        self.reason = reason
        self.message = message

    def construct(self):
        details = {}
        if self.message:
            details['message'] = self.message

        self.message = [
            Message.GOODBYE, details, self.reason
        ]

    def deconstruct(self, payload):
        return payload
