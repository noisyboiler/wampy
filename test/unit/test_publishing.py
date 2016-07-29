import eventlet
import pytest

from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.exceptions import WampyError
from wampy import Peer
from wampy.entrypoints import subscribe


def assert_stops_raising(
        fn, exception_type=Exception, timeout=5, interval=0.1):

    with eventlet.Timeout(timeout):
        while True:
            try:
                fn()
            except exception_type:
                pass
            else:
                return
            eventlet.sleep(interval)


class SubscribingClient(Peer):

    call_count = 0

    @subscribe(topic="foo")
    def foo_topic_handler(self, **kwargs):
        self.call_count += 1


@pytest.yield_fixture
def foo_subscriber(router):
    peer = SubscribingClient(
        name="subscribe", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    peer.start()
    yield peer
    peer.stop()


def test_cannot_publish_nothing_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = Peer(
        name="publisher", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    client.start()
    with pytest.raises(WampyError):
        client.publish(topic="foo")

    assert foo_subscriber.call_count == 0


def test_cannot_publish_args_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = Peer(
        name="publisher", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    client.start()

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

    client = Peer(
        name="publisher", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

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

    class SubscribingClient(Peer):
        received_kwargs = None

        @subscribe(topic="foo")
        def foo_topic_handler(self, **kwargs):
            SubscribingClient.received_kwargs = kwargs

    reader = SubscribingClient(
        name="reader", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    assert SubscribingClient.received_kwargs is None

    with reader:
        assert SubscribingClient.received_kwargs is None

        publisher = Peer(
            name="publisher", router=router,
            realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
        )

        assert SubscribingClient.received_kwargs is None

        with publisher:
            publisher.publish(
                topic="foo", message="foobar", spam="eggs")

            def check_kwargs():
                assert SubscribingClient.received_kwargs == {
                    "message": "foobar",
                    "spam": "eggs"
                }

            assert_stops_raising(check_kwargs)
