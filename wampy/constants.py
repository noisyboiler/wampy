import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'wampy/config.yaml')

CALLEE = 'CALLEE'
CALLER = 'CALLER'
DEALER = 'DEALER'

DEFAULT_REALM = "realm1"

# Basic Profile
DEFAULT_ROLES = {
    'roles': {
        'subscriber': {},
        'publisher': {},
    },
}

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8080

WEBSOCKET_VERSION = 13
WEBSOCKET_SUBPROTOCOLS = 'wamp.2.json'
WEBSOCKET_SUCCESS_STATUS = 101
