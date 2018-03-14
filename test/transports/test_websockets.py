from collections import OrderedDict

import pytest
import gevent
from gevent import Greenlet
from geventwebsocket import (
    WebSocketApplication, WebSocketServer, Resource,
)
from mock import ANY
from mock import call, patch

from wampy.transports.websocket.connection import WebSocket
from wampy.transports.websocket.frames import Ping


class TestApplication(WebSocketApplication):
    pass


@pytest.fixture
def server():
    s = WebSocketServer(
        ('0.0.0.0', 8001),
        Resource(OrderedDict([('/', TestApplication)]))
    )
    s.start()
    thread = Greenlet.spawn(s.serve_forever)
    yield s
    s.stop()
    thread.kill()


def __test_websocket_connects_to_server(server):
    websocket = WebSocket(server_url='ws://0.0.0.0:8001')
    websocket.connect()

    assert len(server.clients) == 1

    websocket.disconnect()


def test_send_ping(server):
    websocket = WebSocket(server_url='ws://0.0.0.0:8001')
    with patch.object(websocket, 'handle_ping') as mock_handle:
        assert websocket.connected is False

        websocket.connect(upgrade=False)

        def connection_handler():
            while True:
                try:
                    websocket.receive()
                except Exception as exc:
                    print(exc)
                    raise

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

        frame = Ping()
        payload = frame.generate_frame()
        socket.send(payload)

        websocket.receive()

        with gevent.Timeout(1):
            while mock_handle.call_count != 1:
                gevent.sleep(0.01)

        assert mock_handle.call_count == 1
        assert mock_handle.call_args == call(ping_frame=ANY)

        call_param = mock_handle.call_args[1]['ping_frame']
        assert isinstance(call_param, Ping)
