import json
import logging

from wampy.errors import WampProtocolError


logger = logging.getLogger(__name__)


class MessageError(Exception):
    pass


class Message(object):
    HELLO = 1
    WELCOME = 2
    ABORT = 3
    GOODBYE = 6

    ERROR = 8

    PUBLISH = 16
    SUBSCRIBE = 32
    SUBSCRIBED = 33
    EVENT = 36

    REGISTER = 64
    REGISTERED = 65
    UNREGISTER = 66
    UNREGISTERED = 67
    INVOCATION = 68

    RESULT = 50

    CALL = 48
    YIELD = 70

    def __init__(self):
        self.serialized = False

    def process(self, client):
        pass

    def serialize(self):
        if self.message is None:
            raise MessageError(
                'cannot serialise unconstructed message'
            )

        self.serialized = True

        try:
            return json.dumps(
                self.message, separators=(',', ':'), ensure_ascii=False,
            )
        except TypeError:
            logger.exception(
                "failed to serialise message: %s", self.message)
            raise WampProtocolError(
                "Message not serialized: {}".format(self.message))
