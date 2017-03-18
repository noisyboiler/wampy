import pytest
from mock import Mock, call

from wampy.constants import DEFAULT_REALM
from wampy.peers.clients import Client
from wampy.roles.callee import CalleeProxy
from wampy.testing.helpers import wait_for_registrations

from test.helpers import assert_stops_raising


class TestRpcProxy(object):

    @pytest.yield_fixture
    def caller(self, router):
        with Client(router=router) as client:
            yield client

    def test_proxy_multiple_callees(self, router, caller):
        call_count = 0

        def my_callback(*args, **kwargs):
            global call_count
            call_count += 1

        procedure_names = [
            "moon", "sun", "fire", "water", "dandelions",
        ]

        factory = CalleeProxy(
            router=router,
            realm=DEFAULT_REALM,
            procedure_names=procedure_names,
            callback=my_callback,
        )

        with factory:
            global call_count

            def wait_for_message():
                assert call_count == 5

            wait_for_registrations(factory, 5)

            with caller:
                caller.rpc.moon("moon")
                caller.rpc.sun("sun")
                caller.rpc.fire("fire")
                caller.rpc.water("water")
                caller.rpc.dandelions("dandelions")

            assert_stops_raising(wait_for_message)
