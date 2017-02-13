from wampy.messages.message import Message


class Goodbye(Message):
    """ Send a GOODBYE message to the Router.

    Message is of the format ``[GOODBYE, Details|dict, Reason|uri]``, e.g. ::

        [
            GOODBYE, {}, "wamp.close.normal"
        ]

    """
    WAMP_CODE = 6
    DEFAULT_REASON = "wamp.close.normal"

    def __init__(
            self, wamp_code, details=None, reason=DEFAULT_REASON,
    ):
        assert wamp_code == self.WAMP_CODE

        self.details = details or {}
        self.reason = reason

        self.message = [
            Message.GOODBYE, self.details, self.reason
        ]
