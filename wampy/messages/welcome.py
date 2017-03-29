import logging

from wampy.errors import WampError
from wampy.messages.message import Message

logger = logging.getLogger(__name__)


class Welcome(Message):
    """ A _Router_ completes the opening of a WAMP session by sending a
   "WELCOME" reply message to the _Client_.

       [WELCOME, Session|id, Details|dict]

    """
    WAMP_CODE = 2

    def __init__(self, wamp_code, session_id, details_dict):
        assert wamp_code == self.WAMP_CODE

        self.session_id = session_id
        self.details = details_dict

        self.message = [
            self.WAMP_CODE, self.session_id, self.details,
        ]

    def process(self, message, client):
        session = client.session
        # response message must be either WELCOME or ABORT
        wamp_code, session_id, _ = message
        if wamp_code not in [Message.WELCOME, Message.ABORT]:
            raise WampError(
                'unexpected response from HELLO message: {}'.format(
                    message
                )
            )

        session.session_id = session_id
        logger.info("WELCOME message recieved")
