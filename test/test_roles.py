import pytest

from wampy.constants import DEFAULT_REALM
from wampy.peers.clients import DefaultClient as Client
from wampy.roles.subscriber import TopicSubscriber

from test.helpers import assert_stops_raising


class TestTopicSubscriber(object):

    @pytest.yield_fixture
    def publisher(self, router):
        with Client() as client:
            yield client

    def test_subscribe_to_topic(self, router, publisher):
        subscriber = TopicSubscriber(
            router=router, realm=DEFAULT_REALM, topic="foo")

        def wait_for_message():
            message = subscriber.messages.pop()
            assert message == "bar"

        with subscriber:
            publisher.publish(topic="foo", message="bar")
            assert_stops_raising(wait_for_message)
