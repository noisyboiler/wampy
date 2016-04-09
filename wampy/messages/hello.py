from . import Message


class Hello(Message):
    """ Send a HELLO message to the Router.

    Message is of the format ``[HELLO, Realm|uri, Details|dict]``, e.g. ::

        [
            HELLO, "realm", {
                "roles": {"subscriber": {}, "publisher": {}},
            }
        ]

    """
    WAMP_CODE = 1

    def __init__(self, realm, roles):
        super(Hello, self).__init__()

        self.realm = realm
        self.roles = roles

    def construct(self):
        self.message = [
            Message.HELLO, self.realm, self.roles
        ]

    def deconstruct(self, payload):
        # A Router will announce the *roles* it supports via
        # Welcome.Details.roles|dict", with a key mapping to a
        # Welcome.Details.roles.<role>|dict" where "<role>" can
        # be: broker, dealer
        message_type = payload[0]
        message = Message.MESSAGE_TYPE_MAP[message_type]
        session_id = payload[1]
        dealer_roles = payload[2]

        return message, session_id, dealer_roles
