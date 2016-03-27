import json
from abc import ABCMeta
from abc import abstractmethod


class MessageError(Exception):
    pass


MESSAGE_TYPE_MAP = {
    1: 'HELLO',
    2: 'WELCOME',
    3: 'ABORT',
    6: 'GOODBYE',
    8: 'ERROR',
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
    __metaclass__ = ABCMeta

    HELLO = 1
    WELCOME = 2
    ABORT = 3
    GOODBYE = 6

    ERROR = 8

    RESULT = 50

    REGISTER = 64
    REGISTERED = 65
    UNREGISTER = 66
    UNREGISTERED = 67
    INVOCATION = 68

    CALL = 48
    YIELD = 70

    def __init__(self):
        self.message = None
        self.serialized = False

    @abstractmethod
    def construct(self, *args, **kwargs):
        """ construct the WAMP message """

    @abstractmethod
    def deconstruct(self):
        """ deconstruct the WAMP message """

    def serialize(self):
        if self.message is None:
            raise MessageError(
                'cannot serialise unconstructed message'
            )

        self.serialized = True

        return json.dumps(
            self.message, separators=(',', ':'), ensure_ascii=False,
        )
