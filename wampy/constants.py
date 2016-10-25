DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8080

WEBSOCKET_VERSION = 13
WEBSOCKET_SUBPROTOCOLS = 'wamp.2.json'
WEBSOCKET_SUCCESS_STATUS = 101

CALLEE = 'CALLEE'
CALLER = 'CALLER'
DEALER = 'DEALER'

ROLES = [
    CALLER, CALLEE, DEALER
]

# Basic Profile
DEFAULT_REALM = "realm1"
DEFAULT_ROLES = {
    'roles': {
        'subscriber': {},
        'publisher': {},
        'callee': {
            'shared_registration': True,
        },
        'caller': {},
    },
}

SUBSCRIBER = "subscriber"
