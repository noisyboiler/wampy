import datetime
from datetime import date

import pytest

from wampy.entrypoints import rpc
from wampy import Peer


class DateService(Peer):

    @rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class HelloService(Peer):

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
    with DateService(name="Date Service"):
        yield


@pytest.yield_fixture
def hello_service(router):
    with HelloService(name="Hello Service"):
        yield


def test_call_with_no_args_or_kwargs(date_service, router):
    client = Peer(name="Caller")
    with client:
        response = client.rpc.get_todays_date()

    today = date.today()

    assert response == today.isoformat()


def test_call_with_args_but_no_kwargs(hello_service, router):
    caller = Peer(name="Caller")
    with caller:
        response = caller.rpc.say_hello("Simon")

    assert response == "Hello Simon"


def test_call_with_no_args_but_a_default_kwarg(hello_service, router):
    caller = Peer(name="Caller")
    with caller:
        response = caller.rpc.say_greeting("Simon")

    assert response == "hola to Simon"


def test_call_with_no_args_but_a_kwarg(hello_service, router):
    caller = Peer(name="Caller")
    with caller:
        response = caller.rpc.say_greeting("Simon", greeting="goodbye")

    assert response == "goodbye to Simon"
