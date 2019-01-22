import logging
from collections import OrderedDict

import pytest
import gevent
from gevent import Greenlet
from geventwebsocket import (
    WebSocketApplication, WebSocketServer, Resource,
)
from mock import ANY
from mock import call, patch

from wampy.backends import async_adapter
from wampy.config.defaults import async_name
from wampy.constants import GEVENT
from wampy.peers.clients import Client
from wampy.testing.helpers import wait_for_session
from wampy.transports.websocket.connection import WebSocket
from wampy.transports.websocket.frames import Close, Ping

logger = logging.getLogger(__name__)

gevent_only = pytest.mark.skipif(
    async_name != GEVENT,
    reason="requires a Greenlet WebSocket server and you're using eventlet"
)


class WsApplication(WebSocketApplication):
    pass


@pytest.fixture
def server():
    s = WebSocketServer(
        ('0.0.0.0', 8001),
        Resource(OrderedDict([('/', WsApplication)]))
    )
    s.start()
    thread = Greenlet.spawn(s.serve_forever)
    yield s
    s.stop()
    thread.kill()


def test_wampy_webscoket_headers(router):
    expected_method_and_path = 'GET / HTTP/1.1'
    expected_headers = {
        'Host': 'localhost:8080',
        'Upgrade': 'websocket',
        'Connection': 'Upgrade',
        'Sec-WebSocket-Key': ANY,
        'Origin': 'ws://localhost:8080',
        'Sec-WebSocket-Version': '13',
        'Sec-WebSocket-Protocol': 'wamp.2.json',
    }

    ws = WebSocket(server_url=router.url)
    header_list = ws._get_handshake_headers(upgrade=True)

    method_and_path = header_list[0]
    actual_headers = {
        header.split(':', 1)[0]: header.split(':', 1)[1].strip()
        for header in header_list[1:]
    }

    assert expected_method_and_path == method_and_path
    assert expected_headers == actual_headers


@gevent_only
def test_send_ping(server):
    websocket = WebSocket(server_url='ws://0.0.0.0:8001')
    with patch.object(websocket, 'handle_ping') as mock_handle:
        assert websocket.connected is False

        websocket.connect(upgrade=False)

        def connection_handler():
            while True:
                try:
                    message = websocket.receive()
                except Exception:
                    logger.exception('connection handler exploded')
                    raise
                if message:
                    logger.info('got message: %s', message)

        assert websocket.connected is True

        # the first bytes sent down the connection are the response bytes
        # to the TCP connection and upgrade. we receieve in this thread
        # because it will block all execution
        Greenlet.spawn(connection_handler)
        gevent.sleep(0.01)  # enough for the upgrade to happen

        clients = server.clients
        assert len(clients) == 1

        client_handler = list(clients.values())[0]
        socket = client_handler.ws

        ping_frame = Ping()
        socket.send(ping_frame.frame)

        with gevent.Timeout(5):
            while mock_handle.call_count != 1:
                gevent.sleep(0.01)

        assert mock_handle.call_count == 1
        assert mock_handle.call_args == call(ping_frame=ANY)

        call_param = mock_handle.call_args[1]['ping_frame']
        assert isinstance(call_param, Ping)


@pytest.fixture(scope="function")
def config_path():
    return './wampy/testing/configs/crossbar.timeout.json'


def test_respond_to_ping_with_pong(config_path, router):
    # This test shows proper handling of ping/pong keep-alives
    # by connecting to a pong-demanding server (crossbar.timeout.json)
    # and keeping the connection open for longer than the server's timeout.
    # Failure would be an exception being thrown because of the server
    # closing the connection.

    class MyClient(Client):
        pass

    exceptionless = True

    try:
        client = MyClient(url=router.url)
        client.start()
        wait_for_session(client)

        async_adapter.sleep(5)

        # this is purely to demonstrate we can make calls while sending
        # pongs
        client.publish(topic="test", message="test")
        client.stop()
    except Exception as e:
        print(e)
        exceptionless = False

    assert exceptionless


@gevent_only
def test_server_closess(server):
    websocket = WebSocket(server_url='ws://0.0.0.0:8001')
    with patch.object(websocket, 'handle_close') as mock_handle:
        websocket.connect(upgrade=False)

        def connection_handler():
            while True:
                try:
                    message = websocket.receive()
                except Exception:
                    logger.exception('connection handler exploded')
                    raise
                if message:
                    logger.info('got message: %s', message)

        Greenlet.spawn(connection_handler)
        gevent.sleep(0.01)  # enough for the upgrade to happen

        clients = server.clients
        client_handler = list(clients.values())[0]
        socket = client_handler.ws
        Greenlet.spawn(socket.close)

        with gevent.Timeout(1):
            while mock_handle.call_count != 1:
                gevent.sleep(0.01)

        assert mock_handle.call_count == 1
        assert mock_handle.call_args == call(close_frame=ANY)

        call_param = mock_handle.call_args[1]['close_frame']
        assert isinstance(call_param, Close)


def test_pinging(router):
    with patch('wampy.transports.websocket.connection.heartbeat', 1):
        with patch(
            'wampy.transports.websocket.connection.heartbeat_timeout', 2
        ):
            client = Client(router.url)
            client.start()
            wait_for_session(client)

            assert client.is_pinging

            ws = client.session.connection
            assert ws.missed_pongs == 0

            async_adapter.sleep(10)

            assert ws.missed_pongs == 0

    client.stop()


@pytest.mark.parametrize(
    "heartbeat, heartbeat_timeout, sleep, expected_missed_pongs", [
        (5, 0, 10, 2),
        (2, 1, 10, 4),
    ]
)
def test_pings_and_missed_pongs(
    router, heartbeat, heartbeat_timeout, sleep, expected_missed_pongs
):
    with patch('wampy.transports.websocket.connection.heartbeat', heartbeat):
        with patch(
            'wampy.transports.websocket.connection.heartbeat_timeout',
            heartbeat_timeout
        ):
            with Client(url=router.url) as client:
                wait_for_session(client)

                assert client.is_pinging is True

                ws = client.session.connection
                assert ws.missed_pongs == 0

                # this prevents Pongs being put into the shared queue
                with patch.object(ws, 'handle_pong'):
                    async_adapter.sleep(sleep)

            assert client.is_pinging is False

    assert ws.missed_pongs == expected_missed_pongs
