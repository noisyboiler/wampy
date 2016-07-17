import datetime
from datetime import date

import pytest

from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.rpc import rpc
from wampy.peers.clients import WampClient, RpcClient


class DateService(WampClient):

    @rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class HelloService(WampClient):

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
    with DateService(
        name="Date Service", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES
    ):

        yield


@pytest.yield_fixture
def hello_service(router):
    with HelloService(
        name="Hello Service", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES
    ):

        yield


def test_call_with_no_args_or_kwargs(date_service, router):
    client = RpcClient(
        name="Caller", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    with client:
        response = client.rpc.get_todays_date()

    today = date.today()

    assert response == today.isoformat()


def test_call_with_args_but_no_kwargs(hello_service, router):
    caller = RpcClient(
        name="Caller", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    caller.start()

    response = caller.rpc.say_hello("Simon")

    assert response == "Hello Simon"

    caller.stop()


def test_call_with_no_args_but_a_default_kwarg(hello_service, router):
    caller = RpcClient(
        name="Caller", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    caller.start()

    response = caller.rpc.say_greeting("Simon")

    assert response == "hola to Simon"

    caller.stop()


def test_call_with_no_args_but_a_kwarg(hello_service, router):
    caller = RpcClient(
        name="Caller", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    caller.start()

    response = caller.rpc.say_greeting("Simon", greeting="goodbye")

    assert response == "goodbye to Simon"

    caller.stop()
