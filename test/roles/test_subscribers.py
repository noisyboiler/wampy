import pytest

from wampy.peers.clients import Client
from wampy.roles.subscriber import TopicSubscriber
from wampy.testing.helpers import wait_for_subscriptions

from test.helpers import assert_stops_raising


class TestTopicSubscriber(object):

    @pytest.yield_fixture
    def publisher(self, router):
        with Client(router=router) as client:
            yield client

    def test_subscribe_to_topics(self, router, publisher):
        global call_count
        call_count = 0

        def my_callback(*args, **kwargs):
            global call_count
            call_count += 1

        subscriber = TopicSubscriber(
            router=router, callback=my_callback, topics=["foo", "spam"]
        )

        with subscriber:
            def wait_for_messages():
                assert call_count == 2

            wait_for_subscriptions(subscriber, 2)

            publisher.publish(topic="foo", message="bar")
            publisher.publish(topic="spam", message="ham")

            assert_stops_raising(wait_for_messages)
