import pytest

from wampy import Peer
from wampy.roles.subscriber import subscribe
from test.helpers import assert_stops_raising


class MetaClient(Peer):

    def __init__(self, *args, **kwargs):
        super(MetaClient, self).__init__(*args, **kwargs)

        self.on_create_call_count = 0
        self.on_subscribe_call_count = 0
        self.on_unsubscribe_call_count = 0
        self.on_delete_call_count = 0

    @subscribe(topic="wamp.subscription.on_create")
    def on_create_handler(self, *args, **kwargs):
        self.on_create_call_count += 1

    @subscribe(topic="wamp.subscription.on_subscribe")
    def on_subscribe_handler(self, *args, **kwargs):
        self.on_subscribe_call_count += 1

    @subscribe(topic="wamp.subscription.on_unsubscribe")
    def on_unsubscribe_handler(self, *args, **kwargs):
        self.on_unsubscribe_call_count += 1

    @subscribe(topic="wamp.subscription.on_delete")
    def on_delete_handler(self, *args, **kwargs):
        self.on_delete_call_count += 1



@pytest.yield_fixture
def publisher(router):
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

    def test_on_create(self, publisher, meta_subscriber):

        class ClientPeer(Peer):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        subscriber = ClientPeer(name="subscriber")

        assert meta_subscriber.on_create_call_count == 0

        with subscriber:
            # the client has started and as subscribed to the
            # topic (but not yet received a message on the topic)

            def check_call_count():
                assert meta_subscriber.on_create_call_count == 1

            assert_stops_raising(check_call_count)

    def test_on_subscribe(self, publisher, meta_subscriber):

        class ClientPeer(Peer):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        subscriber = ClientPeer(name="subscriber")

        assert meta_subscriber.on_subscribe_call_count == 0

        with subscriber:
            publisher.publish(topic="foo", message="ham and eggs")

            def check_call_count():
                assert meta_subscriber.on_subscribe_call_count == 1

            assert_stops_raising(check_call_count)

    def test_on_unsubscribe(self, publisher, meta_subscriber):

        class ClientPeer(Peer):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        subscriber = ClientPeer(name="subscriber")

        assert meta_subscriber.on_unsubscribe_call_count == 0

        with subscriber:
            pass

        def check_call_count():
            assert meta_subscriber.on_unsubscribe_call_count == 1
            # and because this is the last session attached
            assert meta_subscriber.on_delete_call_count == 1

        assert_stops_raising(check_call_count)


class TestMetaProcedures:

    def test_subscription_list(self, publisher):
        class ClientPeer(Peer):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        class AnotherPeer(Peer):
            pass

        subscriber = ClientPeer(name="subscriber")
        another_peer = AnotherPeer(name="another one")

        assert len(subscriber.subscription_map) == 0

        with subscriber:
            assert len(subscriber.subscription_map) == 1

            with another_peer:
                subscription_list = another_peer.call("wamp.subscription.list")
                subscribers = subscription_list['exact']
                assert len(subscribers) == 1
                assert subscribers[0] in subscriber.subscription_map
                assert subscriber.subscription_map[subscribers[0]] == (
                    ClientPeer, 'foo_handler', 'foo')

        assert len(subscriber.subscription_map) == 0


class TestWampyMeta:

    def test_global_subscription_list(self):
        class SubscribingClientPeer(Peer):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        subscribing_client = SubscribingClientPeer(
            name="a subscribing wampy client")
        another_subscribing_client = SubscribingClientPeer(
            name="another subscribing wampy client")

        just_a_client = Peer(name="just a peer")

        assert len(subscribing_client.subscription_map) == 0
        assert len(another_subscribing_client.subscription_map) == 0
        assert len(just_a_client.subscription_map) == 0

        just_a_client.start()
        assert len(just_a_client.subscription_map) == 0

        with subscribing_client:
            assert len(subscribing_client.subscription_map) == 1
            assert len(another_subscribing_client.subscription_map) == 0

            def check_global_list():
                assert len(just_a_client.subscription_map) == 1

            assert_stops_raising(check_global_list)

            with another_subscribing_client:
                assert len(subscribing_client.subscription_map) == 1
                assert len(another_subscribing_client.subscription_map) == 1

                def check_global_list():
                    assert len(just_a_client.subscription_map) == 2

                assert_stops_raising(check_global_list)

        just_a_client.stop()
        assert len(just_a_client.subscription_map) == 0

        assert len(subscribing_client.subscription_map) == 0
        assert len(another_subscribing_client.subscription_map) == 0
