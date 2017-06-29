# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
from datetime import date

import pytest

from wampy.peers.clients import Client
from wampy.roles.callee import callee
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
        """ Return the binary format for a given base ten integer.
        """
        result = bin(integer)
        return result


@pytest.yield_fixture
def date_service(router):
    with DateService(router=router) as serv:
        wait_for_registrations(serv, 1)
        yield


@pytest.yield_fixture
def hello_service(router):
    with HelloService(router=router):
        yield


@pytest.yield_fixture
def binary_number_service(router):
    with BinaryNumberService(router=router):
        yield


class TestClientCall:

    def test_call_with_no_args_or_kwargs(self, date_service, router):
        client = Client(router=router)
        with client:
            response = client.call("get_todays_date")

        today = date.today()

        assert response == today.isoformat()

    def test_call_with_args_but_no_kwargs(self, hello_service, router):
        caller = Client(router=router)
        with caller:
            response = caller.call("say_hello", "Simon")

        assert response == "Hello Simon"

    def test_call_with_args_and_kwargs(self, hello_service, router):
        caller = Client(router=router)
        with caller:
            response = caller.call("say_greeting", "Simon", greeting="watcha")

        assert response == "watcha to Simon"


class TestClientRpc:

    def test_rpc_with_no_args_but_a_default_kwarg(self, hello_service, router):
        caller = Client(router=router)
        with caller:
            response = caller.rpc.say_greeting("Simon")

        assert response == "hola to Simon"

    def test_rpc_with_args_but_no_kwargs(self, hello_service, router):
        caller = Client(router=router)
        with caller:
            response = caller.rpc.say_hello("Simon")

        assert response == "Hello Simon"

    def test_rpc_with_no_args_but_a_kwarg(self, hello_service, router):
        caller = Client(router=router)
        with caller:
            response = caller.rpc.say_greeting("Simon", greeting="goodbye")

        assert response == "goodbye to Simon"
