from wampy.messages.message import Message


class Registered(Message):
    """ [REGISTERED, REGISTER.Request|id, Registration|id]
    """
    WAMP_CODE = 65

    def __init__(self, wamp_code, request_id, registration_id):
        assert wamp_code == self.WAMP_CODE

        self.request_id = request_id
        self.registration_id = registration_id

        self.message = [
            self.WAMP_CODE, self.request_id, self.registration_id,
        ]
