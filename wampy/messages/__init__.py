import json
import logging

from wampy.errors import WampProtocolError


logger = logging.getLogger(__name__)


class MessageError(Exception):
    pass


MESSAGE_TYPE_MAP = {
    1: 'HELLO',
    2: 'WELCOME',
    3: 'ABORT',
    6: 'GOODBYE',
    8: 'ERROR',
    16: 'PUBLISH',
    32: 'SUBSCRIBE',
    33: 'SUBSCRIBED',
    36: 'EVENT',
    48: 'CALL',
    50: 'RESULT',
    64: 'REGISTER',
    65: 'REGISTERED',
    66: 'UNREGISTER',
    67: 'UNREGISTERED',
    68: 'INVOCATION',
    70: 'YIELD',
}


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
        self.message = None
        self.serialized = False

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
