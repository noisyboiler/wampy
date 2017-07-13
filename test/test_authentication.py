# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from wampy.peers.clients import Client
from wampy.roles.callee import callee


@pytest.fixture(scope="function")
def config_path():
    return './wampy/testing/configs/crossbar.static.auth.json'


class FooService(Client):

    @callee
    def get_foo(self, *args, **kwargs):
        return "foo"


@pytest.yield_fixture
def foo_service(router, config_path):
    with FooService(router=router):
        yield


def test_connect(router):
    with Client(router=router, name="unauthenticated-caller") as client:
        client.rpc.get_foo()
