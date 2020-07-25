import eventlet
import gevent
import pytest
from mock import Mock, patch

from wampy.backends import get_async_adapter
from wampy.backends.eventlet_ import Eventlet as EventletAdapter
from wampy.backends.gevent_ import Gevent as GeventAdapter

from wampy.errors import WampyError, WampyTimeOutError


def test_get_unknown_backend():
    with patch('wampy.backends.async_name', 'foobar'):
        with pytest.raises(WampyError):
            get_async_adapter()


class TestGeventadapter:

    def test_get_backend(self):
        adapter = get_async_adapter()
        assert str(adapter) == 'GeventAsyncAdapter'

    def test_interface(self):
        adapter = get_async_adapter()

        assert isinstance(adapter.queue(), gevent.queue.Queue)
        assert adapter.QueueEmpty is gevent.queue.Empty

        timeout = adapter.Timeout(timeout=10)
        assert isinstance(timeout, gevent.Timeout)

    def test_receive_message_g(self):
        mock_queue = Mock()
        mock_queue.qsize.side_effect = [3, 2, 1]
        mock_queue.get.side_effect = [1, 2, 3]

        adapter = GeventAdapter(message_queue=mock_queue)

        message = adapter.receive_message(timeout=1)
        assert message == 1

        message = adapter.receive_message(timeout=1)
        assert message == 2

        message = adapter.receive_message(timeout=1)
        assert message == 3

    def test_receive_message_timeout(self):
        mock_queue = Mock()
        mock_queue.qsize.return_value = 0

        adapter = GeventAdapter(message_queue=mock_queue)

        with pytest.raises(WampyTimeOutError):
            adapter.receive_message(timeout=1)


class TestEventletadapter:

    def test_get_eventlet_backend(self):
        with patch('wampy.backends.async_name', 'eventlet'):
            adapter = get_async_adapter()

        assert str(adapter) == 'EventletAsyncAdapter'

    def test_interface(self):
        with patch('wampy.backends.async_name', 'eventlet'):
            adapter = get_async_adapter()

        assert isinstance(adapter.queue(), eventlet.queue.Queue)
        assert adapter.QueueEmpty is eventlet.queue.Empty

        timeout = adapter.Timeout(timeout=10)
        assert isinstance(timeout, eventlet.Timeout)

    def test_receive_message(self):
        mock_queue = Mock()
        mock_queue.qsize.side_effect = [3, 2, 1]
        mock_queue.get.side_effect = [1, 2, 3]

        adapter = EventletAdapter(message_queue=mock_queue)

        message = adapter.receive_message(timeout=1)
        assert message == 1

        message = adapter.receive_message(timeout=1)
        assert message == 2

        message = adapter.receive_message(timeout=1)
        assert message == 3

    def test_receive_message_timeout(self):
        mock_queue = Mock()
        mock_queue.qsize.return_value = 0

        adapter = EventletAdapter(message_queue=mock_queue)

        with pytest.raises(WampyTimeOutError):
            adapter.receive_message(timeout=1)
