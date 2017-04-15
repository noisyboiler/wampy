import logging

from wampy.messages.message import Message


logger = logging.getLogger('wampy.messages.error')


class Error(Message):
    WAMP_CODE = 8

    def __init__(
            self, wamp_code, request_type, request_id, details, error,
            args_list=None, kwargs_dict=None
    ):
        """ Error reply sent by a Peer as an error response to
        different kinds of requests.

            [ERROR, REQUEST.Type|int, REQUEST.Request|id, Details|dict,
                Error|uri]

            [ERROR, REQUEST.Type|int, REQUEST.Request|id, Details|dict,
                Error|uri, Arguments|list]

            [ERROR, REQUEST.Type|int, REQUEST.Request|id, Details|dict,
                Error|uri, Arguments|list, ArgumentsKw|dict]
        """
        assert wamp_code == self.WAMP_CODE

        self.wamp_code = wamp_code
        self.request_type = request_type
        self.request_id = request_id
        self.details = details
        self.error = error
        self.args_list = args_list
        self.kwargs_dict = kwargs_dict

    def process(self, client=None):
        logger.error(self.error)
