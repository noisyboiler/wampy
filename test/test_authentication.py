# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest

from wampy.errors import WelcomeAbortedError, WampyError
from wampy.messages.message import Message
from wampy.peers.clients import Client
from wampy.roles.callee import callee

from wampy.testing.helpers import (
    CollectingMessageHandler, wait_for_messages)


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
            'callee': {},
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


def test_connection_exits_if_missing_client_secret(router):
    roles = {
        'roles': {
            'subscriber': {},
            'publisher': {},
            'callee': {},
            'caller': {},
        },
        'authmethods': ['wampcra'],
        'authid': 'peter',
    }

    client = Client(
        router=router, roles=roles, name="unauthenticated-client")

    with pytest.raises(WampyError) as exc_info:
        client.start()

    exception = exc_info.value

    message = str(exception)
    assert "WAMPYSECRET" in message


def test_connection_is_challenged(router):
    os.environ['WAMPYSECRET'] = "prq7+YkJ1/KlW1X0YczMHw=="
    roles = {
        'roles': {
            'subscriber': {},
            'publisher': {},
            'callee': {},
            'caller': {},
        },
        'authmethods': ['wampcra'],
        'authid': 'peter',
    }

    message_handler = CollectingMessageHandler()
    client = Client(
        router=router,
        roles=roles,
        message_handler=message_handler,
        name="unauthenticated-client"
    )

    client.start()
    messages = wait_for_messages(client, 2)

    # expect a Challenge and Welcome message
    assert messages[0][0] == Message.CHALLENGE
    assert messages[1][0] == Message.WELCOME

    client.stop()

    # now also expect a Goodbye message
    assert len(messages) == 3
    assert messages[0][0] == Message.CHALLENGE
    assert messages[1][0] == Message.WELCOME
    assert messages[2][0] == Message.GOODBYE
