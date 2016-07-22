import eventlet
import pytest

from wampy.peers.clients import PublishingClient
from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.peers.clients import WampClient
from wampy.publishing import subscriber


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


class SubscribingClient(WampClient):

    call_count = 0

    @subscriber(topic="foo")
    def foo_topic_handler(self, topic_data):
        self.call_count += 1


@pytest.yield_fixture
def foo_subscriber(router):
    peer = SubscribingClient(
        name="subscriber", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    peer.start()
    yield peer
    peer.stop()


def test_publish_nothing_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = PublishingClient(
        name="publisher", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    client.start()
    client.publish(topic="foo")

    def check_call_count():
        assert foo_subscriber.call_count == 1

    assert_stops_raising(check_call_count)


def test_publish_arg_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = PublishingClient(
        name="publisher", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    client.start()
    client.publish("foo", "foobar")

    def check_call_count():
        assert foo_subscriber.call_count == 1

    assert_stops_raising(check_call_count)

    client.stop()


def test_publish_args_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = PublishingClient(
        name="publisher", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    client.start()
    client.publish("foo", "foobar", "spam", "ham", "hmmm")

    def check_call_count():
        assert foo_subscriber.call_count == 1

    assert_stops_raising(check_call_count)

    client.stop()


def test_publish_kwargs_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = PublishingClient(
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
