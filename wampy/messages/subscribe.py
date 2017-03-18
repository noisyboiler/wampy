import random

from wampy.messages.message import Message


class Subscribe(Message):
    """ Send a SUBSCRIBE message to the Router.

    Message is of the format ``[SUBSCRIBE, Request|id, Options|dict,
    Topic|uri]``, e.g. ::

        [
            32, 713845233, {}, "com.myapp.mytopic1"
        ]

    """
    WAMP_CODE = 32

    def __init__(self, topic, options=None):
        super(Subscribe, self).__init__()

        self.topic = topic
        self.options = options or {}
        self.request_id = random.getrandbits(32)
        self.message = [
            self.WAMP_CODE, self.request_id, self.options, self.topic
        ]
