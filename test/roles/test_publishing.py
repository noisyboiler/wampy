# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import pytest
from mock import ANY

from wampy.errors import WampyError
from wampy.peers.clients import Client
from wampy.roles.subscriber import subscribe
from wampy.testing.helpers import assert_stops_raising


logger = logging.getLogger('wampy.testing')


class SubscribingClient(Client):

    call_count = 0

    @subscribe(topic="foo")
    def foo_topic_handler(self, *args, **kwargs):
        self.call_count += 1


@pytest.yield_fixture
def foo_subscriber(router):
    client = SubscribingClient(router=router)
    with client:
        yield client


def test_cannot_publish_nothing_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = Client(router=router)

    with client:
        with pytest.raises(WampyError):
            client.publish(topic="foo")

        assert foo_subscriber.call_count == 0


def test_cannot_publish_args_to_topic(foo_subscriber, router):
    assert foo_subscriber.call_count == 0

    client = Client(router=router)

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

    client = Client(router=router)

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

    reader = SubscribingClient(router=router)

    assert SubscribingClient.received_kwargs is None

    with reader:
        assert SubscribingClient.received_kwargs is None

        publisher = Client(router=router)

        assert SubscribingClient.received_kwargs is None

        with publisher:
            publisher.publish(
                topic="foo", message="foobar", spam="eggs")

            def check_kwargs():
                assert SubscribingClient.received_kwargs == {
                    'message': 'foobar',
                    'spam': 'eggs',
                    'meta': {
                        'topic': 'foo',
                        'subscription_id': ANY,
                    },
                }

            assert_stops_raising(check_kwargs)
