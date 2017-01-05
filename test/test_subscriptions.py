import pytest
from mock import ANY

from wampy.peers.clients import DefaultClient as Client
from wampy.roles.subscriber import subscribe
from test.helpers import assert_stops_raising


class MetaClient(Client):

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
    client = Client()
    client.start()
    client.publish(topic="foo", message="bar")
    yield client
    client.stop()


@pytest.yield_fixture
def meta_subscriber(router):
    client = MetaClient()
    with client:
        yield client


class TestMetaEvents:

    def test_on_create(self, publisher, meta_subscriber):

        class FooClient(Client):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        subscriber = FooClient()

        assert meta_subscriber.on_create_call_count == 0

        with subscriber:
            # the client has started and as subscribed to the
            # topic (but not yet received a message on the topic)

            def check_call_count():
                assert meta_subscriber.on_create_call_count == 1

            assert_stops_raising(check_call_count)

    def test_on_subscribe(self, publisher, meta_subscriber):

        class FooClient(Client):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        subscriber = FooClient()

        assert meta_subscriber.on_subscribe_call_count == 0

        with subscriber:
            publisher.publish(topic="foo", message="ham and eggs")

            def check_call_count():
                assert meta_subscriber.on_subscribe_call_count == 1

            assert_stops_raising(check_call_count)

    def test_on_unsubscribe(self, publisher, meta_subscriber):

        class FooClient(Client):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        subscriber = FooClient()

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
        class FooClient(Client):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        # two clients are the same subscription ID in the router, and so
        # two subscribers to the same topic should give a subscription
        # list with a single item only
        foo_subscriber = FooClient()
        another_foo_subscriber = FooClient()

        assert len(foo_subscriber.subscription_map) == 0
        assert len(another_foo_subscriber.subscription_map) == 0

        class SpamClientClient(Client):
            @subscribe(topic="spam")
            def spam_handler(self, **kwargs):
                pass

        spam_subscriber = SpamClientClient()

        with foo_subscriber:
            foo_subscription_id, topic = foo_subscriber.subscription_map[
                'foo_handler']

            def check_list():
                subscription_list = foo_subscriber.get_subscription_list()
                assert len(subscription_list['exact']) == 1
                assert foo_subscription_id in subscription_list['exact']
                assert topic == "foo"

            assert_stops_raising(check_list)

            with another_foo_subscriber:
                another_subscription_id, topic = (
                    another_foo_subscriber.subscription_map['foo_handler']
                )

                assert another_subscription_id == foo_subscription_id

                def check_list():
                    subscription_list = (
                        another_foo_subscriber.get_subscription_list()
                    )
                    assert len(subscription_list['exact']) == 1
                    assert another_subscription_id in subscription_list[
                        'exact']
                    assert topic == "foo"

                assert_stops_raising(check_list)

                with spam_subscriber:
                    # now there are 3 clients and 2 subscriptions

                    spam_subscription_id, _ = spam_subscriber.subscription_map[
                        'spam_handler']

                    def check_list():
                        subscription_list = (
                            spam_subscriber.get_subscription_list()
                        )
                        assert len(subscription_list['exact']) == 2

                        assert (
                            foo_subscription_id in subscription_list['exact'])
                        assert (
                            spam_subscription_id in subscription_list['exact'])

                    assert_stops_raising(check_list)

        assert len(foo_subscriber.subscription_map) == 0
        assert len(another_foo_subscriber.subscription_map) == 0
        assert len(spam_subscriber.subscription_map) == 0

    def test_get_subscription_match(self, router):
        class FooClient(Client):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        # two clients are the same subscription ID in the router....
        foo_subscriber = FooClient()
        another_foo_subscriber = FooClient()

        assert len(foo_subscriber.subscription_map) == 0
        assert len(another_foo_subscriber.subscription_map) == 0

        just_a_client = Client()

        with foo_subscriber:
            with another_foo_subscriber:
                foo_subscription_ids = foo_subscriber.get_subscription_match(
                    topic="foo")
                assert len(foo_subscription_ids) == 1

                another_foo_subscription_ids = (
                    foo_subscriber.get_subscription_match(topic="foo"))
                assert len(another_foo_subscription_ids) == 1

                assert foo_subscription_ids == another_foo_subscription_ids

                with just_a_client:
                    def check_list():
                        subscription_list = (
                            just_a_client.get_subscription_list())
                        assert len(subscription_list['exact']) == 1
                        assert (
                            subscription_list['exact'] ==
                            foo_subscription_ids
                        )
                        assert (
                            subscription_list['exact'] ==
                            another_foo_subscription_ids
                        )

                    assert_stops_raising(check_list)

    def test_subscription_lookup(self, router):
        class FooClient(Client):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        foo_subscriber = FooClient()

        assert len(foo_subscriber.subscription_map) == 0

        with foo_subscriber:
            subscription_id = foo_subscriber.get_subscription_lookup(
                topic="foo")
            assert subscription_id is not None

            foo_subscription_id, topic = foo_subscriber.subscription_map[
                'foo_handler']
            assert topic == "foo"
            assert subscription_id == foo_subscription_id

    def test_subscription_lookup_topic_not_found(self, router):
        class FooClient(Client):
            pass

        client = FooClient()
        with client:
            subscription_id = client.get_subscription_lookup(topic="spam")
            assert subscription_id is None

    def test_get_subscription_info(self, router):
        class FooClient(Client):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        foo_subscriber = FooClient()
        another_foo_subscriber = FooClient()

        just_a_client = Client()

        with foo_subscriber:
            with another_foo_subscriber:
                with just_a_client:
                    subscription_id, _ = foo_subscriber.subscription_map[
                        'foo_handler']
                    info = just_a_client.get_subscription_info(
                            subscription_id=subscription_id)

        expected_info = {
            'created': ANY,
            'uri': 'foo',
            'match': 'exact',
            'id': subscription_id,
        }

        assert expected_info == info

    def test_list_subscribers(self, router):
        class FooClient(Client):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        foo_subscriber = FooClient()
        another_foo_subscriber = FooClient()

        just_a_client = Client()

        with foo_subscriber:
            with another_foo_subscriber:
                expected_subscribers = sorted(
                    [
                        foo_subscriber.session.id,
                        another_foo_subscriber.session.id,
                    ]
                )

                with just_a_client:
                    subscription_id = just_a_client.get_subscription_lookup(
                        topic="foo")
                    subscribers = just_a_client.list_subscribers(
                        subscription_id=subscription_id)

        assert expected_subscribers == sorted(subscribers)

    def test_count_subscribers(self, router):
        class FooClient(Client):
            @subscribe(topic="foo")
            def foo_handler(self, **kwargs):
                pass

        foo_subscriber = FooClient()
        another_foo_subscriber = FooClient()

        just_a_client = Client()

        with foo_subscriber:
            with another_foo_subscriber:
                with just_a_client:
                    subscription_id = just_a_client.get_subscription_lookup(
                        topic="foo")
                    subscriptions = just_a_client.count_subscribers(
                        subscription_id=subscription_id)

        assert subscriptions == 2
