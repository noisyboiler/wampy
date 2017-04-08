from wampy.messages.handlers.invocation import InvokeWithMetaMessageHandler
from wampy.roles.callee import CalleeProxy
from wampy.testing.helpers import wait_for_registrations

from test.helpers import assert_stops_raising


class TestInvokeWithMeta(object):

    def test_handler(self, router, client):
        call_count = 0
        procedure_names = ["foo", "bar", "spam"]

        def callback(*args, **kwarsg):
            global call_count
            call_count += 1

        proxy = CalleeProxy(
            router=router,
            procedure_names=procedure_names,
            callback=callback,
            message_handler=InvokeWithMetaMessageHandler,
        )

        with proxy:
            global call_count
            wait_for_registrations(proxy, 3)

            def wait_for_calls():
                assert call_count == 3

            client.rpc.foo()
            client.rpc.bar()
            client.rpc.spam()

            assert_stops_raising(wait_for_calls)
