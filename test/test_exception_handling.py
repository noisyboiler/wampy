# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from wampy.errors import RemoteError
from wampy.peers.clients import Client
from wampy.roles.callee import callee


class UnreliableCallee(Client):

    @callee
    def get_foo(self, *args, **kwargs):
        raise ValueError(
            "i don't like any of your values: %s, %s", args, kwargs
        )


@pytest.yield_fixture
def unreliable_callee(router, config_path):
    with UnreliableCallee(router=router):
        yield


def test_handle_value_error(unreliable_callee, router):
    with Client(router=router) as client:

        with pytest.raises(RemoteError):
            client.rpc.get_foo(1, 2, three=3)
