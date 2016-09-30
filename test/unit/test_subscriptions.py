import pytest

from wampy import Peer
from wampy.entrypoints import subscribe
from test.helpers import assert_stops_raising


class MetaClient(Peer):

    call_count = 0

    @subscribe(topic="wamp.subscription.on_create")
    def on_create_handler(self, *args, **kwargs):
        self.call_count += 1


@pytest.yield_fixture
def publisher_without_subscribers(router):
    client = Peer(name="publisher")
    client.start()
    client.publish(topic="foo", message="bar")
    yield client
    client.stop()


@pytest.yield_fixture
def meta_subscriber(router):
    peer = MetaClient(name="subscriber")

    peer.start()
    yield peer
    peer.stop()


class TestMetaEvents:

    def test_subscription_on_create(
            self, publisher_without_subscribers, meta_subscriber
    ):

        class ClientPeer(Peer):
            @subscribe(topic="foo")
            def on_subscribe_handler(self, **kwargs):
                pass

        subscriber = ClientPeer(name="subscriber")

        with subscriber:

            def check_call_count():
                assert meta_subscriber.call_count == 1

            assert_stops_raising(check_call_count)
