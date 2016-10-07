import datetime
from datetime import date

import pytest

from wampy.roles.callee import rpc
from wampy import Client


class DateService(Client):

    @rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class HelloService(Client):

    @rpc
    def say_hello(self, name):
        message = "Hello {}".format(name)
        return message

    @rpc
    def say_greeting(self, name, greeting="hola"):
        message = "{greeting} to {name}".format(
            greeting=greeting, name=name)
        return message


@pytest.yield_fixture
def date_service(router):
    with DateService(name="date service"):
        yield


@pytest.yield_fixture
def hello_service(router):
    with HelloService(name="hello service"):
        yield


def test_call_with_no_args_or_kwargs(date_service, router):
    client = Client(name="just a client")
    with client:
        response = client.rpc.get_todays_date()

    today = date.today()

    assert response == today.isoformat()


def test_call_with_args_but_no_kwargs(hello_service, router):
    caller = Client(name="just a client")
    with caller:
        response = caller.rpc.say_hello("Simon")

    assert response == "Hello Simon"


def test_call_with_no_args_but_a_default_kwarg(hello_service, router):
    caller = Client(name="Caller")
    with caller:
        response = caller.rpc.say_greeting("Simon")

    assert response == "hola to Simon"


def test_call_with_no_args_but_a_kwarg(hello_service, router):
    caller = Client(name="Caller")
    with caller:
        response = caller.rpc.say_greeting("Simon", greeting="goodbye")

    assert response == "goodbye to Simon"
