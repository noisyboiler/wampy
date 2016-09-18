import pytest

from wampy import Peer
from wampy.entrypoints import subscribe
from test.helpers import assert_stops_raising



class MetaSubscribingClient(Peer):

    call_count = 0

    @subscribe(topic="wamp.subscription.on_create")
    def on_create_handler(self, **kwargs):
        self.call_count += 1

    @subscribe(topic="wamp.subscription.on_subscribe")
    def on_subscribe_handler(self, **kwargs):
        self.call_count += 1



@pytest.yield_fixture
def meta_subscriber(router):
    peer = MetaSubscribingClient(name="subscriber")

    peer.start()
    yield peer
    peer.stop()


class TestMetaEvents:

    def test_subscription_on_create(self, meta_subscriber):
        assert meta_subscriber.call_count == 0

        client = Peer(name="publisher")
        with client:
            client.publish(topic="foo", message="bar")

        def check_call_count():
            assert meta_subscriber.call_count == 1

        assert_stops_raising(check_call_count)
