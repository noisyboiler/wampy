# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Hello(object):
    """ Send a HELLO message to the Router.

    By default the *wampy* Client announces support for all four Client
    Roles: Subscriber, Publisher, Callee and Caller.

    Message is of the format ``[HELLO, Realm|uri, Details|dict]``, e.g. ::

        [
            HELLO, "realm", {
                "roles": {
                    "subscriber": {
                        'features': {...},
                    },
                    "publisher": {...},
                    ...
                },
                "authmethods": ["wampcra"],
                "authid": "peter"
            }
        ]

    """
    WAMP_CODE = 1
    name = "hello"

    def __init__(self, realm, details):
        super(Hello, self).__init__()

        self.realm = realm
        self.details = details

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.realm, self.details
        ]
