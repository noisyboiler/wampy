import pytest
from mock import ANY

from wampy.peers.clients import Client
from wampy.roles.subscriber import subscribe
from wampy.errors import WampyError

from test.helpers import assert_stops_raising


class SubscribingClient(Client):

    call_count = 0

    @subscribe(topic="foo")
    def foo_topic_handler(self, **kwargs):
        self.call_count += 1


@pytest.yield_fixture
def foo_subscriber(router):
    client = SubscribingClient()
    with client:
        yield client


def test_cannot_publish_nothing_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = Client()

    with client:
        with pytest.raises(WampyError):
            client.publish(topic="foo")

        assert foo_subscriber.call_count == 0


def test_cannot_publish_args_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = Client()

    with client:

        with pytest.raises(WampyError):
            client.publish("foo",)

        assert foo_subscriber.call_count == 0

        with pytest.raises(WampyError):
            client.publish("foo", "foobar")

        assert foo_subscriber.call_count == 0

        even_more_args = range(100)

        with pytest.raises(WampyError):
            client.publish(even_more_args)

        assert foo_subscriber.call_count == 0


def test_publish_kwargs_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = Client()

    client.start()
    client.publish(topic="foo", message="foobar")

    def check_call_count():
        assert foo_subscriber.call_count == 1

    assert_stops_raising(check_call_count)

    client.publish(topic="foo", message="foobar")
    client.publish(topic="foo", message="spam")
    client.publish(topic="foo", message="ham")

    def check_call_count():
        assert foo_subscriber.call_count == 4

    assert_stops_raising(check_call_count)

    client.stop()


def test_kwargs_are_received(router):

    class SubscribingClient(Client):
        received_kwargs = None

        @subscribe(topic="foo")
        def foo_topic_handler(self, **kwargs):
            SubscribingClient.received_kwargs = kwargs

    reader = SubscribingClient()

    assert SubscribingClient.received_kwargs is None

    with reader:
        assert SubscribingClient.received_kwargs is None

        publisher = Client()

        assert SubscribingClient.received_kwargs is None

        with publisher:
            publisher.publish(
                topic="foo", message="foobar", spam="eggs")

            def check_kwargs():
                assert SubscribingClient.received_kwargs == {
                    'message': 'foobar',
                    'spam': 'eggs',
                    '_meta': {
                        'topic': 'foo',
                        'subscription_id': ANY,
                    },
                }

            assert_stops_raising(check_kwargs)


def test_subscribing_client_will_not_get_old_messages(router):

    class SubscribingClient(Client):

        call_count = 0

        @subscribe(topic="foo")
        def foo_topic_handler(self, **kwargs):
            self.call_count += 1

    # don't start this client yet
    subscriber = SubscribingClient()

    publisher = Client()
    with publisher:
        publisher.publish(topic="foo", message="foobar")
        publisher.publish(topic="foo", message="foobar")
        publisher.publish(topic="foo", message="spam")
        publisher.publish(topic="foo", message="ham")

        with subscriber:
            def check_call_count():
                assert subscriber.call_count == 0

            assert_stops_raising(check_call_count)

            publisher.publish(topic="foo", message="more ham")

            def check_call_count():
                logger.info("call count: %s", subscriber.call_count)
                print(
                    "call count: {}".format(subscriber.call_count)
                )
                assert subscriber.call_count == 5

            print("check call count")
            assert_stops_raising(check_call_count)
