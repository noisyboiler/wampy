# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8080

CROSSBAR_DEFAULT = "ws://{}/{}".format(DEFAULT_HOST, DEFAULT_PORT)

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
# TODO: this encapsulates more than just "roles", while "features"
# should really be passed in here too, e.g. `call_timeout`. This was
# not fully understood when first desigining the API.
DEFAULT_ROLES = {
    'roles': {
        'subscriber': {},
        'publisher': {},
        'callee': {
            'shared_registration': True,
        },
        'caller': {
            'features': {
                'call_timeout': True,
            }
        },
    },
    'authmethods': ['anonymous']
}
DEFAULT_TIMEOUT = 10  # seconds

# disabled by default. override with OS env variables.
DEFAULT_HEARTBEAT_SECONDS = 0
DEFAULT_HEARTBEAT_TIMEOUT_SECONDS = 2

SUBSCRIBER = "subscriber"

# WAMP URIs
NOT_AUTHORISED = 'wamp.error.not_authorized'

GEVENT = 'gevent'
EVENTLET = 'eventlet'
EVENT_LOOP_BACKENDS = [EVENTLET, GEVENT]
