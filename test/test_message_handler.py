from wampy.messages.handler import MessageHandler
from wampy.messages.invocation import InvocationWithMeta
from wampy.messages import Goodbye, Error, Registered, Welcome
from wampy.roles.callee import CalleeProxy
from wampy.testing.helpers import wait_for_registrations

from test.helpers import assert_stops_raising


class InvokeWithMetaMessageHandler(MessageHandler):

    def __init__(self, client):
        super(InvokeWithMetaMessageHandler, self).__init__(
            client=client, messages_to_handle=[
                InvocationWithMeta, Welcome, Registered, Goodbye, Error
            ]
        )


class TestInvokeWithMeta(object):

    def test_handler(self, router, client):
        global call_count
        call_count = 0

        procedure_names = ["foo", "bar", "spam"]

        def callback(*args, **kwargs):
            assert "meta" in kwargs
            assert kwargs['meta']['procedure_name'] in procedure_names
            assert kwargs['meta']['session_id']
            assert kwargs['meta']['request_id']

            global call_count
            call_count += 1
            return "spam"

        with CalleeProxy(
            router=router,
            procedure_names=procedure_names,
            callback=callback,
            message_handler=InvokeWithMetaMessageHandler,
        ) as proxy:

            wait_for_registrations(proxy, 3)

            def wait_for_calls():
                assert call_count == 3

            result1 = client.rpc.foo()
            result2 = client.rpc.bar()
            result3 = client.rpc.spam()

            assert_stops_raising(wait_for_calls)

            assert result1 == result2 == result3 == "spam"
