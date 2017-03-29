import datetime
from datetime import date

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


def test_call_with_no_args_or_kwargs(date_service, router):
    client = Client(router=router)
    with client:
        response = client.rpc.get_todays_date()

    today = date.today()

    assert response == today.isoformat()


def test_call_with_args_but_no_kwargs(hello_service, router):
    caller = Client(router=router)
    with caller:
        response = caller.rpc.say_hello("Simon")

    assert response == "Hello Simon"


def test_call_with_no_args_but_a_default_kwarg(hello_service, router):
    caller = Client(router=router)
    with caller:
        response = caller.rpc.say_greeting("Simon")

    assert response == "hola to Simon"


def test_call_with_no_args_but_a_kwarg(hello_service, router):
    caller = Client(router=router)
    with caller:
        response = caller.rpc.say_greeting("Simon", greeting="goodbye")

    assert response == "goodbye to Simon"
