# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
from datetime import date

import pytest

from wampy.backends import get_async_adapter
from wampy.errors import WampyTimeOutError
from wampy.peers.clients import Client
from wampy.roles.callee import callee
from wampy.roles import callee as alt_callee  # alt_calee should be the same with callee
from wampy.testing import wait_for_registrations


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
        result = bin(integer)
        return result


class ReallySlowService(Client):

    @callee
    def requires_patience(self, wait_in_seconds):
        async_ = get_async_adapter()
        async_.sleep(wait_in_seconds)
        reward_for_waiting = "$$$$"
        return reward_for_waiting


@pytest.fixture
def date_service(router):
    with DateService(url=router.url) as serv:
        wait_for_registrations(serv, 1)
        yield


@pytest.fixture
def hello_service(router):
    with HelloService(url=router.url):
        yield


@pytest.fixture
def binary_number_service(router):
    with BinaryNumberService(url=router.url):
        yield


@pytest.fixture
def really_slow_service(router):
    with ReallySlowService(url=router.url):
        yield


def test_alternative_callee_import_style():
    assert callee is alt_callee


class TestClientCall:

    def test_call_with_no_args_or_kwargs(self, date_service, router):
        client = Client(url=router.url)
        with client:
            response = client.call("get_todays_date")

        today = date.today()

        assert response == today.isoformat()

    def test_call_with_args_but_no_kwargs(self, hello_service, router):
        caller = Client(url=router.url)
        with caller:
            response = caller.call("say_hello", "Simon")

        assert response == "Hello Simon"

    def test_call_with_args_and_kwargs(self, hello_service, router):
        caller = Client(url=router.url)
        with caller:
            response = caller.call("say_greeting", "Simon", greeting="watcha")

        assert response == "watcha to Simon"


class TestClientRpc:

    def test_rpc_with_no_args_but_a_default_kwarg(self, hello_service, router):
        caller = Client(url=router.url)
        with caller:
            response = caller.rpc.say_greeting("Simon")

        assert response == "hola to Simon"

    def test_rpc_with_args_but_no_kwargs(self, hello_service, router):
        caller = Client(url=router.url)
        with caller:
            response = caller.rpc.say_hello("Simon")

        assert response == "Hello Simon"

    def test_rpc_with_no_args_but_a_kwarg(self, hello_service, router):
        caller = Client(url=router.url)
        with caller:
            response = caller.rpc.say_greeting("Simon", greeting="goodbye")

        assert response == "goodbye to Simon"


class TestCallerTimeout:
    @pytest.mark.parametrize("call_timeout, wait, reward", [
        (1, 2, None),
        (2, 1, "$$$$"),
        (0.9, 1.1, None),
        (1, 3, None),
    ])
    def test_timeout_values(
        self, call_timeout, wait, reward, router, really_slow_service,
    ):
        with Client(url=router.url, call_timeout=call_timeout) as client:
            try:
                resp = client.rpc.requires_patience(wait_in_seconds=wait)
            except WampyTimeOutError:
                resp = None

        assert resp == reward
