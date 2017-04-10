import logging

from wampy.messages.message import Message

logger = logging.getLogger(__name__)


class Registered(Message):
    """ [REGISTERED, REGISTER.Request|id, Registration|id]
    """
    WAMP_CODE = 65

    def __init__(self, wamp_code, request_id, registration_id):
        assert wamp_code == self.WAMP_CODE

        self.wamp_code = wamp_code
        self.request_id = request_id
        self.registration_id = registration_id

        self.message = [
            self.WAMP_CODE, self.request_id, self.registration_id,
        ]

    def process(self, client):
        session = client.session
        procedure_name = client.request_ids[self.request_id]
        session.registration_map[self.registration_id] = procedure_name

        logger.info(
            'Registered procedure name "%s"', procedure_name,
        )
