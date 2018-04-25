# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from wampy.errors import WampyError
from wampy.peers.clients import Client
from wampy.roles.callee import callee


class UnreliableCallee(Client):

    @callee
    def get_foo(self, *args, **kwargs):
        raise ValueError(
            "i do not like any of your values: {}, {}".format(
                args, kwargs)
        )


@pytest.yield_fixture
def unreliable_callee(router, config_path):
    with UnreliableCallee(router=router):
        yield


def test_handle_value_error(unreliable_callee, router):
    with Client(router=router, name="caller") as client:

        with pytest.raises(WampyError) as exc_info:
            client.rpc.get_foo(1, 2, three=3)

        exception = exc_info.value
        assert type(exception) is WampyError

        message = str(exception)

        assert "i do not like any of your values" in message
        assert "(1, 2)" in message
        assert "three" in message
