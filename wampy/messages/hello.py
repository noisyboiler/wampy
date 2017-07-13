# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from wampy.messages.message import Message


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
    name = "hello"

    def __init__(self, realm, roles):
        super(Hello, self).__init__()

        self.realm = realm
        self.roles = roles

        self.message = [
            Message.HELLO, self.realm, self.roles
        ]
