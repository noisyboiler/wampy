import pytest
from mock import Mock, call
from mock import ANY

from wampy.constants import DEFAULT_REALM
from wampy.peers.clients import Client
from wampy.roles.subscriber import TopicSubscriber

from test.helpers import assert_stops_raising


class TestTopicSubscriber(object):

    @pytest.yield_fixture
    def publisher(self, router):
        with Client(router=router) as client:
            yield client

    def test_subscribe_to_topics(self, router, publisher):
        message_handler = Mock()

        subscriber = TopicSubscriber(
            router=router, realm=DEFAULT_REALM, topics=["foo", "spam"],
            message_handler=message_handler)

        def wait_for_message():
            assert message_handler.call_count == 2
            assert message_handler.call_args_list == [
                call(_meta={
                    'topic': 'foo', 'subscription_id': ANY}, message=u'bar'),
                call(_meta={
                    'topic': 'spam', 'subscription_id': ANY}, message=u'ham'),
            ]

        with subscriber:
            publisher.publish(topic="foo", message="bar")
            publisher.publish(topic="spam", message="ham")
            assert_stops_raising(wait_for_message)
