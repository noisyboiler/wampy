# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime

import pytest

from wampy.peers.clients import Client
from wampy.roles.callee import callee
from wampy.testing.helpers import wait_for_session


class DateService(Client):

    @callee
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class HelloService(Client):

    @callee
    def say_hello(self, name):
        message = "Hello {}".format(name)
        return message

    @callee
    def say_greeting(self, name, greeting="hola"):
        message = "{greeting} to {name}".format(
            greeting=greeting, name=name)
        return message


class BinaryNumberService(Client):

    @callee
    def get_binary(self, integer):
        """ Return the binary format for a given base ten integer.
        """
        result = bin(integer)
        return result


@pytest.yield_fixture
def date_service(router):
    with DateService(router=router):
        yield


@pytest.yield_fixture
def hello_service(router):
    with HelloService(router=router):
        yield


@pytest.yield_fixture
def binary_number_service(router):
    with BinaryNumberService(router=router):
        yield


def make_service_clients(router, ids):
    clients = []
    for id_ in ids:
        clients.append(Client(router=router, id=id_))

    return clients


def test_client_connects_to_router(router):
    class MyClient(Client):
        pass

    client = MyClient(router=router)

    assert client.session.id is None

    client.start()
    wait_for_session(client)

    session = client.session
    assert session.id is not None
    assert session.client is client

    client.stop()

    assert client.session.id is None


def test_can_start_two_clients(router):

    class MyClient(Client):
        pass

    app_one = MyClient(router=router)
    app_one.start()
    wait_for_session(app_one)

    assert app_one.session.id

    app_two = MyClient(router=router)
    app_two.start()
    wait_for_session(app_two)

    assert app_two.session.id

    app_one.stop()
    app_two.stop()

    assert app_one.session.id is None
    assert app_two.session.id is None
