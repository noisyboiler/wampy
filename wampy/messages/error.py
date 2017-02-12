from wampy.messages.message import Message


class Error(Message):
    WAMP_CODE = 8

    def __init__(self, wamp_code, *args, **kwargs):
        assert wamp_code == self.WAMP_CODE
