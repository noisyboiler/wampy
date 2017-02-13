import logging

from wampy.messages.message import Message


logger = logging.getLogger('wampy.messages.error')


class Error(Message):
    WAMP_CODE = 8

    def __init__(self, wamp_code, *args, **kwargs):
        assert wamp_code == self.WAMP_CODE

    def process(self, message, client=None):
        _, _, _, _, _, errors = message
        logger.error(errors)
