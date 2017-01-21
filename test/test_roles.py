import pytest
from mock import Mock, call

from wampy.constants import DEFAULT_REALM
from wampy.peers.clients import Client
from wampy.roles.subscriber import TopicSubscriber

from test.helpers import assert_stops_raising


class TestTopicSubscriber(object):

    @pytest.yield_fixture
    def publisher(self, router):
        with Client() as client:
            yield client

    def test_subscribe_to_topic(self, router, publisher):
        message_handler = Mock()

        subscriber = TopicSubscriber(
            router=router, realm=DEFAULT_REALM, topic="foo",
            message_handler=message_handler)

        def wait_for_message():
            assert message_handler.called is True
            assert message_handler.call_args == call(u'bar')

        with subscriber:
            publisher.publish(topic="foo", message="bar")
            assert_stops_raising(wait_for_message)
