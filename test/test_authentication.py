# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from wampy.errors import WelcomeAbortedError
from wampy.peers.clients import Client
from wampy.roles.callee import callee


@pytest.fixture(scope="function")
def config_path():
    # this config has some static user creds defined
    # for "peter"
    return './wampy/testing/configs/crossbar.static.auth.json'


class FooService(Client):

    @callee
    def get_foo(self, *args, **kwargs):
        return "foo"


@pytest.yield_fixture
def foo_service(router, config_path):
    with FooService(router=router):
        yield


def test_connection_is_aborted_when_not_authorised(router):
    roles = {
        'roles': {
            'subscriber': {},
            'publisher': {},
            'callee': {
                'shared_registration': True,
            },
            'caller': {},
        },
        'authmethods': ['wampcra'],
        'authid': 'not-an-expected-user',
    }

    client = Client(
        router=router, roles=roles, name="unauthenticated-client")

    with pytest.raises(WelcomeAbortedError) as exc_info:
        client.start()

    exception = exc_info.value

    message = str(exception)

    assert (
        "no principal with authid \"not-an-expected-user\" exists"
        in message
    )
    assert "wamp.error.not_authorized" in message
