# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Hello(object):
    """ Send a HELLO message to the Router.

    Message is of the format ``[HELLO, Realm|uri, Details|dict]``, e.g. ::

        [
            HELLO, "realm", {
                "roles": {"subscriber": {}, "publisher": {}},
                "authmethods": ["wampcra"],
                "authid": "peter"
            }
        ]

    """
    WAMP_CODE = 1
    name = "hello"

    def __init__(self, realm, roles):
        super(Hello, self).__init__()

        self.realm = realm
        self.roles = roles

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.realm, self.roles
        ]
