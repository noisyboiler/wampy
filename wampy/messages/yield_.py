from wampy.messages.message import Message


class Yield(Message):
    """ When the Callee is able to successfully process and finish the
    execution of the call, it answers by sending a "YIELD" message to the
    Dealer.

    Message is of the format ::

        [
            YIELD, INVOCATION.Request|id, Options|dict, Arguments|list,
            ArgumentsKw|dict
        ]

    "INVOCATION.Request" is the ID from the original invocation
    request.

    "Options"is a dictionary that allows to provide additional options.

    "Arguments" is a list of positional result elements (each of
    arbitrary type).  The list may be of zero length.

    "ArgumentsKw" is a dictionary of keyword result elements (each of
    arbitrary type).  The dictionary may be empty.

    """
    WAMP_CODE = 70

    def __init__(
            self, invocation_request_id, options=None, result_args=None,
            result_kwargs=None
    ):

        super(Yield, self).__init__()

        self.invocation_request_id = invocation_request_id
        self.options = options or {}
        self.result_args = result_args or []
        self.result_kwargs = result_kwargs or {}

    @property
    def message(self):
        return [
            Message.YIELD, self.invocation_request_id, self.options,
            self.result_args, self.result_kwargs
        ]
