import pytest
from mock import Mock, call

from wampy.constants import DEFAULT_REALM
from wampy.peers.clients import Client
from wampy.roles.callee import RpcProxy

from test.helpers import assert_stops_raising


class TestRpcProxy(object):

    @pytest.yield_fixture
    def caller(self, router):
        with Client(router=router) as client:
            yield client

    def test_proxy_multiple_callees(self, router, caller):
        callback = Mock()
        procedure_names = [
            "moon", "sun", "fire", "water", "dandelions",
        ]
        callback.return_value = procedure_names

        factory = RpcProxy(
            router=router,
            realm=DEFAULT_REALM,
            procedure_names=procedure_names,
            callback=callback,
        )

        def wait_for_message():
            assert callback.call_count == len(procedure_names)
            assert callback.call_args_list == [
                call("moon"), call("sun"), call("fire"), call("water"),
                call("dandelions")
            ]

        with factory:
            with caller:
                caller.rpc.moon("moon")
                caller.rpc.sun("sun")
                caller.rpc.fire("fire")
                caller.rpc.water("water")
                caller.rpc.dandelions("dandelions")

                assert_stops_raising(wait_for_message)
